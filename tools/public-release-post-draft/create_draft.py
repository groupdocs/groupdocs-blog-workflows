import argparse
import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
import os
import logging
import json
import time

import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# Metrics tracking for token usage and API calls
_metrics = {"token_usage": 0, "api_calls_count": 0}


def _track_usage(response):
    """Extract and accumulate token usage from an API response."""
    _metrics["api_calls_count"] += 1
    if hasattr(response, 'usage') and response.usage:
        _metrics["token_usage"] += getattr(response.usage, 'total_tokens', 0)


@dataclass
class DraftInputs:
    product: str
    version: str
    title: str
    release_notes_url: str
    review_enabled: bool = False
    max_retries: int = 3


def get_model_name() -> str:
    """Get model name from environment variable."""
    return os.getenv("PROFESSIONALIZE_MODEL_NAME", "recommended")


def get_reviewer_model() -> Optional[str]:
    """Get reviewer model name. Returns None if review is disabled."""
    return os.getenv("PROFESSIONALIZE_REVIEWER_MODEL", None)


def create_client() -> OpenAI:
    """Create OpenAI client from environment variables."""
    api_key = os.getenv("PROFESSIONALIZE_API_KEY")
    base_url = os.getenv("PROFESSIONALIZE_API_URL")
    if not api_key:
        raise RuntimeError("Missing PROFESSIONALIZE_API_KEY environment variable")
    if not base_url:
        raise RuntimeError("Missing PROFESSIONALIZE_API_URL environment variable")
    return OpenAI(api_key=api_key, base_url=base_url)


def parse_cli_args(argv: Optional[list[str]] = None) -> DraftInputs:
    parser = argparse.ArgumentParser(description="Generate public release post draft inputs")
    parser.add_argument("--product", required=True, help="Product name, e.g. 'GroupDocs.Viewer for .NET'")
    parser.add_argument("--version", required=True, help="Product version, e.g. '25.9'")
    parser.add_argument("--title", required=True, help="Draft title, e.g. 'September 2025 release'")
    parser.add_argument(
        "--release-notes",
        required=True,
        help=(
            "Link to public release notes, e.g. "
            "'https://releases.groupdocs.com/viewer/net/release-notes/2025/groupdocs-viewer-for-net-25-9-release-notes/'"
        ),
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Enable LLM review suggestions after generating the post (disabled by default)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts when judge model finds issues (default: 3)",
    )

    ns = parser.parse_args(argv)

    url = ns.release_notes.strip()
    # Allow a leading '@' prefix (e.g. copied from chat)
    url = url[1:] if url.startswith("@") else url

    inputs = DraftInputs(product=ns.product, version=ns.version, title=ns.title, release_notes_url=url, review_enabled=bool(ns.review), max_retries=ns.retries)
    logging.debug("Parsed inputs: product='%s', version='%s', title='%s'", inputs.product, inputs.version, inputs.title)
    logging.debug("Release notes URL: %s", inputs.release_notes_url)
    return inputs


def fetch_release_notes_main_html(url: str) -> str:
    logging.info("Fetching release notes from: %s", url)
    headers = {
        "User-Agent": "groupdocs-blog-workflows/1.0 (+https://blog.groupdocs.com)"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    logging.debug("Fetched release notes: status=%s, bytes=%d", resp.status_code, len(resp.text))

    # Force UTF-8: the server often reports ISO-8859-1 but the actual content
    # is UTF-8, causing characters like U+2011 (non-breaking hyphen) in issue
    # IDs to be mangled.
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    main_section = soup.find("section", attrs={"role": "main"})
    if not main_section:
        # Fallback: try main tag or primary content container
        logging.debug("<section role='main'> not found, trying fallbacks <main> or div[role='main']")
        main_section = soup.find("main") or soup.find("div", attrs={"role": "main"})
    if not main_section:
        raise RuntimeError("Could not locate <section role=\"main\"> in the release notes page")

    # Keep inner HTML of the section to preserve structure for LLM context
    # Trim excessive whitespace while preserving tags
    # Note: We avoid aggressive sanitization; downstream can decide how to render.
    html = str(main_section)
    # Remove leading outer tag wrapper, keeping inner content
    # e.g., <section role="main"> ... </section>
    match = re.match(r"^<section[^>]*>([\s\S]*?)</section>\s*$", html, flags=re.IGNORECASE)
    inner = match.group(1) if match else html
    # Normalize non-breaking hyphens (U+2011), soft hyphens (U+00AD), and
    # figure dashes (U+2012) to regular hyphens so issue IDs like
    # VIEWERNET-5551 aren't corrupted when the LLM processes them.
    inner = inner.replace("\u2011", "-").replace("\u00ad", "-").replace("\u2012", "-")
    logging.debug("Extracted main section HTML length: %d", len(inner))
    return inner


def _parse_month_year_from_title(title: str) -> Tuple[Optional[str], Optional[int]]:
    logging.debug("Parsing month/year from title: %s", title)
    m = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
                  title, flags=re.IGNORECASE)
    if not m:
        return None, None
    month_name = m.group(1)
    year = int(m.group(2))
    # Normalize to title case month name (e.g., September)
    norm_month = month_name[:1].upper() + month_name[1:].lower()
    logging.debug("Parsed month/year: %s %s", norm_month, year)
    return norm_month, year


def _slugify(text: str) -> str:
    # Lowercase, replace non alphanum with hyphens, collapse duplicates
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _extract_family_and_platform(product: str) -> Tuple[str, str, str]:
    # product like "GroupDocs.Viewer for .NET" -> family: viewer, product_short: GroupDocs.Viewer, platform_label: .NET
    product_short = product.split(" for ")[0].strip()
    family = product_short.split(".")[-1]
    family_slug = family.lower()
    platform_label = product.split(" for ")[-1].strip() if " for " in product else ""
    return family_slug, product_short, platform_label


def _platform_to_slug(platform_label: str) -> str:
    mapping = {
        ".NET": "net",
        ".NET UI": "net-ui",
        "Java": "java",
        "Node.js": "node-js",
        "Python": "python",
    }
    return mapping.get(platform_label, _slugify(platform_label))


def _version_to_slug(version: str) -> str:
    return version.strip().lower().replace(".", "-")


def build_front_matter_yaml(inputs: DraftInputs) -> str:
    # Derive components
    month_name, year = _parse_month_year_from_title(inputs.title)
    month_year = f"{month_name} {year}" if month_name and year else inputs.title
    family_slug, product_short, platform_label = _extract_family_and_platform(inputs.product)
    platform_slug = _platform_to_slug(platform_label)
    version_slug = _version_to_slug(inputs.version)
    name_slug = f"groupdocs-{family_slug}-for-{platform_slug}-{version_slug}"
    url = f"/{family_slug}/{name_slug}/"
    logging.debug("Front matter slugs: family=%s, platform=%s, version=%s", family_slug, platform_slug, version_slug)
    logging.debug("Post URL: %s", url)

    # Title and SEO
    title = f"{inputs.product} {inputs.version} \u2013 {month_year} Release Highlights"
    seo_title = f"{inputs.product} {inputs.version} \u2013 Latest Updates and Fixes ({month_year})"
    package_manager = {
        ".NET": "NuGet", ".NET UI": "NuGet", "Java": "Maven",
        "Node.js": "npm", "Python": "PyPI",
    }.get(platform_label, "the GroupDocs")
    description = f"Explore what's new in {inputs.product} {inputs.version}. Available now on {package_manager} and GroupDocs website."
    summary = f"{inputs.product} {inputs.version} is here."

    # Date in RFC 1123 format at midnight UTC
    now = datetime.now(timezone.utc)
    rfc1123 = now.strftime("%a, %d %b %Y 00:00:00 +0000")

    # Tags and categories
    tags = [product_short, platform_label, "Releases"] if platform_label else [product_short, "Releases"]
    categories = [f"{product_short} Releases"]

    # Cover
    cover_image = f"{url}images/{name_slug}.png"
    cover_alt = title
    cover_caption = title

    # Render YAML front matter
    # Note: Using explicit newlines and spaces to control formatting precisely.
    tags_joined = ", ".join([f"'{_escape_single_quotes(str(t))}'" for t in tags])
    fm_lines = [
        "---",
        f"title: \"{title}\"",
        f"seoTitle: \"{seo_title}\"",
        f"description: \"{description}\"",
        f"date: {rfc1123}",
        "draft: true",
        f"url: {url}",
        "author: \"GroupDocs Team\"",
        f"summary: \"{summary}\"",
        f"tags: [{tags_joined}]",
        f"categories: ['{categories[0]}']",
        "showToc: true",
        "tocOpen: true",
        "cover:",
        f"    image: {cover_image}",
        f"    alt: \"{cover_alt}\"",
        f"    caption: \"{cover_caption}\"",
        "    hidden: false",
        "---",
    ]
    fm = "\n".join(fm_lines)
    logging.debug("Built front matter length: %d", len(fm))
    return fm


def build_draft_prompt(inputs: DraftInputs, release_notes_html: str) -> str:
    """Build the user prompt for draft generation.

    Structure: all instructions grouped before data blocks. Example templates
    are cleaned of typos and release-specific content so the model learns
    structure and tone without parroting stale details.
    """
    viewer_example_template = (
        "We're happy to announce the release of **{product} {version}**, available as of **{month_year}**. "
        "This release delivers two new features with public API changes, one enhancement, and four bug fixes.\n\n"
        "## What's new in this release\n\n"
        "* **[New feature]** Introduce distinct font type for each format family (VIEWERNET-5486)\n"
        "* **[New feature]** List substituted fonts when getting all fonts for the WordProcessing family formats (VIEWERNET-5484)\n\n"
        "Both features improve the mechanism for extracting and listing fonts used in a loaded document. "
        "With VIEWERNET-5484, GroupDocs.Viewer can now list and return _substitution fonts_ \u2014 fonts not present in the original document "
        "but used to replace missing originals on the target machine. "
        "VIEWERNET-5486 improves the public API: instead of a single `UsedFontInfo` type, there is now an `IFontInfo` interface "
        "with format-family-specific implementations. "
        "See \"[Getting all used fonts in the loaded document](https://docs.groupdocs.com/viewer/net/getting-used-fonts/)\" for details.\n\n"
        "## Fixes and enhancements\n\n"
        "* **[Enhancement]** Embed fonts when converting Spreadsheet documents to embedded HTML. (VIEWERNET-5490)\n"
        "* **[Fix]** PDF attachment in base PDF rendered to HTML with issues. (VIEWERNET-5374)\n"
        "* **[Fix]** Gradient on background is incorrect when rendering PDF to HTML. (VIEWERNET-5345)\n"
        "* **[Fix]** Failed to load specific PSD. (VIEWERNET-3780)\n"
        "* **[Fix]** Wrong page number displayed initially during server delays. (VIEWERNET-5485)\n\n"
        "## How to get the update\n\n"
        "- **NuGet** \u2013 Upgrade to the latest `{product}` package via NuGet. Choose the package for your target platform: "
        "[Cross-platform .NET 6 Package](https://www.nuget.org/packages/GroupDocs.Viewer.CrossPlatform/{version}) or "
        "[Windows-only .NET Framework 4.6.2 and .NET 6 Package](https://www.nuget.org/packages/GroupDocs.Viewer/{version})\n"
        "- **Direct Download** \u2013 Download assemblies from the "
        "[GroupDocs.Viewer for .NET {version}](https://releases.groupdocs.com/viewer/net/new-releases/groupdocs.viewer-for-.net-{version}-dlls-only/) page\n\n"
        "## Resources\n\n"
        "* [Full Release Notes]({release_notes_url})\n"
        "* [Documentation](https://docs.groupdocs.com/viewer/net/)\n"
        "* [Free Support Forum](https://forum.groupdocs.com/c/viewer/9)\n\n"
        "---\n"
    )

    total_example_template = (
        "We're happy to announce the **GroupDocs.Total for .NET {version}** release, available as of **{month_year}**. "
        "This update brings bug fixes and version upgrades of the individual libraries that compose the Total suite.\n\n"
        "## What's new in this release\n\n"
        "The following products were updated in this version:\n\n"
        "* GroupDocs.Conversion for .NET (25.7 \u2192 25.8)\n"
        "* GroupDocs.Viewer for .NET (25.7 \u2192 25.8)\n"
        "* GroupDocs.Comparison for .NET (25.7 \u2192 25.8)\n"
        "* GroupDocs.Metadata for .NET (25.7 \u2192 25.8)\n"
        "* GroupDocs.Parser for .NET (25.7 \u2192 25.8)\n\n"
        "### Fixes\n\n"
        "| Issue | Product | Description |\n"
        "|-------|---------|-------------|\n"
        "| **TOTALNET-204** | Conversion | Fixed incorrect table formatting when converting HTML to PDF. |\n"
        "| **TOTALNET-287** | Annotation | Resolved missing localized string error. |\n"
        "| **TOTALNET-298** | Viewer | Fixed a null-reference exception on diagram rendering. |\n\n"
        "No new public-API features or enhancements were introduced in this release.\n\n"
        "## How to get the update\n\n"
        "### NuGet\n\n"
        "Upgrade the **GroupDocs.Total** package (or the .NET Framework-specific package) to the latest version:\n\n"
        "* [.NET 6](https://www.nuget.org/packages/GroupDocs.Total)\n"
        "* [.NET Framework 4.6.2+](https://www.nuget.org/packages/GroupDocs.Total.NETFramework)\n\n"
        "### Direct download\n\n"
        "Download the compiled assemblies from the "
        "[GroupDocs.Total for .NET {version} download page]"
        "(https://releases.groupdocs.com/total/net/new-releases/groupdocs.total-for-.net-{version}/).\n\n"
        "## Resources\n\n"
        "- [Full release notes]({release_notes_url})\n"
        "- [Documentation](https://docs.groupdocs.com/total/net/)\n"
        "- [Free Support Forum](https://forum.groupdocs.com/c/total/8)\n\n"
        "---\n"
    )

    example_template = total_example_template if "Total" in inputs.product else viewer_example_template

    # Platform-aware package manager for the output skeleton
    family_slug, _, platform_label = _extract_family_and_platform(inputs.product)
    pkg_manager = {
        ".NET": "NuGet", ".NET UI": "NuGet", "Java": "Maven",
        "Node.js": "npm", "Python": "PyPI",
    }.get(platform_label, "Package manager")

    # For Total products, use Issue|Product|Description table with descriptions.
    # For individual products, use the exact Key|Category|Summary format from release notes.
    is_total = "Total" in inputs.product
    if is_total:
        table_instruction = (
            "[Table: Issue | Product | Description]\n"
            "[Brief description per fix from release notes]\n"
        )
    else:
        table_instruction = (
            "[EXACT Key|Category|Summary table from release notes \u2014 "
            "reproduce ALL rows, do NOT rewrite summaries]\n"
        )

    # All instructions grouped before data blocks; CRITICAL RULES style
    # from MCP optimizer testing (numbered constraints > prose instructions).
    prompt = (
        f"Draft a public release blog post for **{inputs.product} v{inputs.version}** "
        f"(title: \"{inputs.title}\").\n\n"
        "**CRITICAL RULES:**\n"
        "1. Use the <release_notes> HTML as the **single source of truth**. "
        "Do NOT invent version numbers, issue IDs, URLs, or technical details "
        "not present in the notes.\n"
        "2. Follow the structure and tone of the <example_template>, adapting names, "
        "links, issue IDs, and counts to match this release.\n"
        "3. ONLY list products whose version actually changed "
        "(the Version column contains an arrow, e.g. \"25.12 -> 26.2\"). "
        "Do NOT list products with unchanged versions.\n"
        "4. Reproduce fix/change descriptions **exactly as written** in the release "
        "notes. Do NOT embellish, add root-cause analysis, or invent details.\n"
        "5. Include code examples from the release notes when present, "
        "using fenced code blocks with the correct language tag.\n"
        "6. Use ONLY links found in the release notes. If a link is not available, "
        "omit it rather than guessing.\n"
        "7. Tone: technical and factual \u2014 no hype, no exclamation marks.\n"
        "8. **Do NOT output YAML front matter.** The <front_matter> is provided for "
        "context only \u2014 it is prepended automatically. "
        "Start your output directly with the opening paragraph.\n\n"
        "**OUTPUT STRUCTURE (follow exactly):**\n\n"
        "[Opening paragraph]\n"
        "## What's new in this release\n"
        f"{table_instruction}"
        "## Public API changes\n"
        "[Verbatim from release notes, if present \u2014 omit section if absent]\n"
        "## New features\n"
        "[Verbatim from release notes, if present \u2014 omit section if absent]\n"
        "## Code example\n"
        "[Fenced code block from release notes, if present \u2014 omit section if absent]\n"
        "## How to get the update\n"
        f"### {pkg_manager}\n"
        f"[{pkg_manager} dependency/links from release notes]\n"
        "### Direct download\n"
        "[Download links from release notes \u2014 omit if absent]\n"
        "## Resources\n"
        "[Links from release notes]\n"
        "---\n\n"
        "<example_template>\n"
        f"{example_template}"
        "</example_template>\n\n"
        "<front_matter>\n"
        f"{build_front_matter_yaml(inputs)}\n"
        "</front_matter>\n\n"
        "<release_notes>\n"
        f"{release_notes_html}\n"
        "</release_notes>\n"
    )
    logging.debug("Built LLM prompt length: %d", len(prompt))
    return prompt


def generate_draft_with_llm(client: OpenAI, prompt: str, feedback_context: str = "") -> str:
    logging.info("Calling LLM to generate draft body...")

    system_content = (
        "You are a professional technical writer specializing in GroupDocs product releases. "
        "Generate ONLY the Markdown body content for a public release blog post "
        "\u2014 NO YAML front matter, NO extra text, NO commentary. "
        "Start directly with the opening paragraph. "
        "Keep all sections complete but concise. "
        "Use ## for top-level sections, ### for subsections."
    )
    if feedback_context:
        system_content += f"\n\n{feedback_context}"

    messages = [
        {
            "role": "system",
            "content": system_content,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    model = get_model_name()
    response = client.chat.completions.create(model=model, messages=messages)
    _track_usage(response)
    content = response.choices[0].message.content.strip()
    logging.debug("LLM response length: %d", len(content))

    # Strip optional BOM and any leading whitespace
    def _strip_possible_front_matter_if_present(text: str) -> str:
        t = text.lstrip("\ufeff\n\r ")
        if t.startswith("---"):
            m = re.search(r"^---[\s\S]*?\n---\s*\n?", t)
            if m:
                logging.debug("Detected and stripped front matter from LLM output during validation")
                return t[m.end():]
        return t

    def _validate_markdown_body(md: str) -> None:
        logging.debug("Validating markdown body: %s", md)
        # Should contain at least one heading or list section to ensure structure
        has_heading = bool(re.search(r"^##\s+.+", md, flags=re.MULTILINE))
        has_list = bool(re.search(r"^\s*[-*+]\s+.+", md, flags=re.MULTILINE))
        if not (has_heading or has_list):
            raise ValueError("Generated content lacks headings or lists expected in a release post.")
        # Should not contain YAML front matter blocks
        # Match YAML front matter: --- on its own line, followed by YAML content (key: value), then --- on its own line
        # This avoids matching horizontal rules (---) or table separators by requiring YAML-like content
        yaml_match = re.search(r"^---\s*\n([\s\S]*?)\n---\s*$", md, flags=re.MULTILINE)
        if yaml_match:
            # Additional check: ensure it looks like YAML (contains key-value pairs with colons)
            content_between = yaml_match.group(1)
            if re.search(r"^\s*\w+\s*:", content_between, flags=re.MULTILINE):
                raise ValueError("Generated content unexpectedly includes YAML front matter.")

    cleaned = _strip_possible_front_matter_if_present(content)
    try:
        _validate_markdown_body(cleaned)
        logging.debug("LLM markdown validation succeeded")
    except Exception as e:
        logging.error("LLM markdown validation failed: %s", e)
        raise

    return content


def review_full_post_with_llm(client: OpenAI, reviewer_model: str,
                              full_post_markdown: str) -> Optional[str]:
    """
    Use a separate judge model to review the generated post.
    Returns None if PASS, or a string with issues if FAIL.
    """
    logging.info("Reviewing full post with judge model (%s)...", reviewer_model)

    review_prompt = (
        "You are reviewing a release blog post draft.\n\n"
        "Check for these issues:\n"
        "1. Does the post have proper markdown structure (## headings, lists, links)?\n"
        "2. Are product names and version numbers accurate and consistent?\n"
        "3. Is the content complete and not truncated?\n"
        "4. Are code examples properly formatted in code blocks?\n"
        "5. Does the post follow the expected sections (What's new, Fixes/Enhancements, How to get, Resources)?\n"
        "6. Are links well-formed and not broken markdown?\n\n"
        "If the post is GOOD, respond with exactly: PASS\n"
        "If there are issues, respond with: FAIL followed by a brief list of specific problems found.\n\n"
        f"POST:\n{full_post_markdown}"
    )

    try:
        response = client.chat.completions.create(
            model=reviewer_model,
            messages=[{"role": "user", "content": review_prompt}],
            temperature=0.1,
        )
        _track_usage(response)
        result = response.choices[0].message.content.strip()
        # Strip <think> blocks from qwen3-style models
        result = re.sub(r'<think>[\s\S]*?</think>', '', result).strip()
        if result.upper().startswith("PASS"):
            return None
        return result
    except Exception as e:
        logging.warning("Review call failed (%s), skipping review", e)
        return None


def refine_front_matter_with_llm(client: OpenAI, model: str,
                                 full_post_markdown: str) -> Dict[str, Any]:
    logging.debug("Improving front matter with LLM (model=%s)", model)

    system_msg = (
        "You are refining YAML front matter for a release blog post. "
        "Review the full post (front matter + body) and propose improved values ONLY for these fields: "
        "seoTitle, description, summary, tags, cover_alt, cover_caption. "
        "Return STRICT JSON with exactly these keys. Do not include any additional text."
    )
    user_msg = (
        "Full post follows. Provide JSON only; for tags return an array of 3-6 concise tags.\n\n"
        "<post>\n"
        f"{full_post_markdown}\n"
        "</post>\n"
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    response = client.chat.completions.create(model=model, messages=messages)
    _track_usage(response)
    raw = response.choices[0].message.content.strip()
    # Strip <think> blocks from qwen3-style models
    raw = re.sub(r'<think>[\s\S]*?</think>', '', raw).strip()
    logging.debug("Front matter improvement JSON length: %d", len(raw))

    # Extract JSON payload (in case model wrapped in code fences)
    m = re.search(r"\{[\s\S]*\}$", raw, flags=re.MULTILINE)
    payload = raw[m.start():] if m else raw
    data = json.loads(payload)

    # Basic validation
    required_keys = ["seoTitle", "description", "summary", "tags", "cover_alt", "cover_caption"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"Front matter improvements missing key: {k}")
    if not isinstance(data.get("tags"), list):
        raise ValueError("'tags' must be an array")

    return data


def _escape_single_quotes(s: str) -> str:
    return s.replace("'", "\\'")


def apply_front_matter_improvements(fm: str, improvements: Dict[str, Any]) -> str:
    # Replace simple scalar fields
    def rep_line(text: str, key: str, value: str) -> str:
        def _escape_double_quotes(s: str) -> str:
            return s.replace('"', '\\"')
        pattern = rf"^(" + re.escape(key) + r":\s*)\"[^\"]*\"\s*$"
        return re.sub(
            pattern,
            lambda m: m.group(1) + f"\"{_escape_double_quotes(value)}\"",
            text,
            flags=re.MULTILINE,
        )

    fm_updated = fm
    fm_updated = rep_line(fm_updated, "seoTitle", improvements.get("seoTitle", ""))
    fm_updated = rep_line(fm_updated, "description", improvements.get("description", ""))
    fm_updated = rep_line(fm_updated, "summary", improvements.get("summary", ""))

    # Update tags list
    tags: List[str] = [str(t) for t in improvements.get("tags", [])]
    tags_escaped = ", ".join([f"'{_escape_single_quotes(t)}'" for t in tags])
    tags_line = f"tags: [{tags_escaped}]"
    fm_updated = re.sub(r"^tags:\s*\[.*?\]\s*$", tags_line, fm_updated, flags=re.MULTILINE)

    # Update cover alt and caption (exact four-space indent as generated)
    def _escape_double_quotes(s: str) -> str:
        return s.replace('"', '\\"')
    cover_alt = _escape_double_quotes(str(improvements.get("cover_alt", "")))
    cover_caption = _escape_double_quotes(str(improvements.get("cover_caption", "")))
    fm_updated = re.sub(r"^\s{4}alt:\s*\"[^\"]*\"\s*$", f"    alt: \"{cover_alt}\"", fm_updated, flags=re.MULTILINE)
    fm_updated = re.sub(r"^\s{4}caption:\s*\"[^\"]*\"\s*$", f"    caption: \"{cover_caption}\"", fm_updated, flags=re.MULTILINE)

    return fm_updated


def split_front_matter_blocks(md: str) -> Tuple[str, str]:
    t = md.lstrip("\ufeff")
    m = re.match(r"^---\n([\s\S]*?)\n---\s*\n?", t)
    if not m:
        raise ValueError("Front matter block not found at document start")
    fm = m.group(0).strip()
    body = t[m.end():]
    return fm, body

def main(argv: Optional[list[str]] = None) -> int:
    try:
        # Basic logging setup; respect LOG_LEVEL if set, default to INFO
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="%(levelname)s %(message)s")
        # Quiet noisy HTTP client loggers
        for _name in ("httpx", "httpcore", "openai", "urllib3", "requests.packages.urllib3", "requests"):
            _logger = logging.getLogger(_name)
            _logger.setLevel(logging.ERROR)
            _logger.propagate = False
        logging.info("Starting draft generation pipeline")
        inputs = parse_cli_args(argv)
        notes_html = fetch_release_notes_main_html(inputs.release_notes_url)
        front_matter = build_front_matter_yaml(inputs)
        prompt = build_draft_prompt(inputs, notes_html)

        # Initialize LLM client
        client = create_client()
        model = get_model_name()
        reviewer_model = get_reviewer_model()

        if reviewer_model:
            logging.info("Judge model: %s (cross-model quality review enabled)", reviewer_model)

        # If the model returned front matter (despite instructions), strip it
        def _strip_front_matter(text: str) -> str:
            t = text.lstrip("\ufeff\n\r ")
            if t.startswith("---"):
                # remove first front matter block
                m = re.search(r"^---[\s\S]*?\n---\s*\n?", t)
                if m:
                    return t[m.end():]
            return t

        # Generate blog body via LLM with retry loop (judge model feedback)
        max_retries = inputs.max_retries
        feedback_context = ""
        body_md = None

        for attempt in range(1, max_retries + 1):
            logging.info("Generation attempt %d/%d", attempt, max_retries)
            body_md = generate_draft_with_llm(client, prompt, feedback_context)

            before_len = len(body_md)
            body_md = _strip_front_matter(body_md).lstrip()
            logging.debug("Post-processed body: before=%d, after=%d", before_len, len(body_md))

            # If no reviewer model, accept the first generation
            if not reviewer_model:
                break

            # Run judge model review
            candidate_md = f"{front_matter}\n\n{body_md}\n"
            review_result = review_full_post_with_llm(client, reviewer_model, candidate_md)
            if review_result is None:
                logging.info("Judge review: PASS")
                break
            elif attempt < max_retries:
                logging.info("Judge review: FAIL (attempt %d) \u2014 %s", attempt, review_result[:200])
                feedback_context = (
                    f"IMPORTANT: A reviewer found these issues in your previous draft: "
                    f"{review_result[:500]}. Fix them in this attempt."
                )
                time.sleep(1)
                continue
            else:
                logging.warning("Judge review: FAIL on final attempt %d \u2014 proceeding anyway", attempt)

        final_md = f"{front_matter}\n\n{body_md}\n"

        # Improve front matter fields using LLM (seoTitle, description, summary, tags, cover alt/caption)
        # Use reviewer model for refinement if available, otherwise main model
        refine_model = reviewer_model or model
        logging.info("Improving front matter fields using LLM (model=%s)...", refine_model)
        try:
            fm_text, body_text = split_front_matter_blocks(final_md)
            improvements = refine_front_matter_with_llm(client, refine_model, final_md)
            improved_fm = apply_front_matter_improvements(fm_text, improvements)
            final_md = f"{improved_fm}\n\n{body_text}"
        except Exception as e:
            logging.error("Front matter improvement failed: %s", e)

        # Save to output/index.md within tool directory
        logging.info("Saving final markdown...")
        out_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        logging.info("Saved final markdown: %s (chars=%d)", out_path, len(final_md))

        # Write metrics for workflow consumption
        metrics_file = os.path.join(out_dir, "draft_metrics.json")
        try:
            with open(metrics_file, 'w') as f:
                json.dump(_metrics, f)
            logging.info("Token usage: %d, API calls: %d", _metrics['token_usage'], _metrics['api_calls_count'])
        except Exception as e:
            logging.warning("Could not write metrics file: %s", e)

        # Review the complete post and print suggestions (optional)
        if inputs.review_enabled and reviewer_model:
            review_result = review_full_post_with_llm(client, reviewer_model, final_md)
            if review_result:
                print("\nReviewer suggestions:\n")
                print(review_result)
            else:
                print("\nReviewer: PASS \u2014 no issues found.")
        return 0
    except Exception as exc:
        logging.error("Error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
