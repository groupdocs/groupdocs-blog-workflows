import argparse
import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timezone
import os
import logging
import json

import requests
from bs4 import BeautifulSoup
from openai import OpenAI


@dataclass
class DraftInputs:
    product: str
    version: str
    title: str
    release_notes_url: str
    review_enabled: bool = False


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

    ns = parser.parse_args(argv)

    url = ns.release_notes.strip()
    # Allow a leading '@' prefix (e.g. copied from chat)
    url = url[1:] if url.startswith("@") else url

    inputs = DraftInputs(product=ns.product, version=ns.version, title=ns.title, release_notes_url=url, review_enabled=bool(ns.review))
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
    logging.debug("Extracted main section HTML length: %d", len(inner))
    return inner


def _parse_month_year_from_title(title: str) -> Tuple[Optional[str], Optional[int]]:
    logging.debug("Parsing month/year from title: %s", title)
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
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
    title = f"{inputs.product} {inputs.version} – {month_year} Release Highlights"
    seo_title = f"{inputs.product} {inputs.version} – Latest Updates and Fixes ({month_year})"
    description = f"Explore what’s new in {inputs.product} {inputs.version}. Available now on NuGet and GroupDocs website."
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
    # Provide the model with clear structure and a concrete example to emulate.
    viewer_example_template = (
        "We’re happy to announce the major release of **{product} {version}**, available as of **{month_year}**. "
        "This major release delivers two new features with public API changes, one enhancement and 4 fixed bug.\n\n"
        "## What’s new in this release\n\n"
        "* **[New feature]** Introduce distinct font type for each formats family (VIEWERNET-5486)\n"
        "* **[New feature]** List substituted fonts when getting all fonts for the WordProcessing family formats (VIEWERNET-5484)\n\n"
        "Both these features continue to improve the mechanism of extracting and listing used fonts of the loaded document. "
        "In short, with VIEWERNET-5484 the GroupDocs.Viewer is now possible to list and return the _substitutuion fonts_, which are not present in original document, "
        "but are used to replace those original fonts, which are missing and thus unavailable on a target machine (where the GroupDocs.Viewer is running). "
        "The VIEWERNET-5486 feature improves the public API — instead of a single `UsedFontInfo` type now there is a `IFontInfo` interfave and a plenty of its inheritors — one per each formats family. "
        "Visit the article \"[Getting all used fonts in the loaded document ](https://docs.groupdocs.com/viewer/net/getting-used-fonts/)\" in public documentation for the further details.\n\n"
        "## Fixes and enhancements\n\n"
        "* **[Enhancement]** Embed fonts when converting Spreadsheet documents to embedded HTML. (VIEWERNET-5490)\n"
        "* **[Fix]** PDF attachment in base PDF in rendered to HTML format with issues. (VIEWERNET-5374)  \n"
        "* **[Fix]** Gradient on background is not correct when rendering PDF to HTML. (VIEWERNET-5345)  \n"
        "* **[Fix]** Failed to load specific PSD. (VIEWERNET-3780)  \n"
        "* **[Fix]** [UI] Groupdocs Viewer 8.0.7 - Wrong page no displayed initially during server delays to return pages. (VIEWERNET-5485)  \n\n"
        "## How to get the update\n\n"
        "- **NuGet** – Upgrade to the latest `{product}` package via NuGet. Choose the package for your target platform: "
        "[Cross-platform .NET 6 Package](https://www.nuget.org/packages/GroupDocs.Viewer.CrossPlatform/{version}) or "
        "[Windows-only .NET Framework 4.6.2 and .NET 6 Package](https://www.nuget.org/packages/GroupDocs.Viewer/{version})  \n"
        "- **Direct Download** – Download assemblies for both .NET and .NET Framework from the "
        "[GroupDocs.Viewer for .NET {version}](https://releases.groupdocs.com/viewer/net/new-releases/groupdocs.viewer-for-.net-{version}-dlls-only/) page\n\n"
        "## Resources\n\n"
        "* [Full Release Notes]({release_notes_url})  \n"
        "* [Documentation](https://docs.groupdocs.com/viewer/net/)  \n"
        "* [GroupDocs.Viewer Free Support Forum](https://forum.groupdocs.com/c/viewer/9)  \n\n"
        "---\n"
    )

    total_example_template = (
        "We’re happy to announce the **GroupDocs.Total for .NET {version}** release, available as of **{month_year}**. "
        "This update brings a few critical bug fixes, an important packaging change, and the usual version upgrades of the individual libraries that compose the Total suite.\n\n"
        "## Important notice\n\n"
        "> Starting with version **25.9**, **GroupDocs.Classification** will no longer be included in the **GroupDocs.Total** package. The library contains large machine-learning model files, which significantly increase the overall package size and may affect performance for users who do not need classification features.  \n"
        "> If your project requires classification, you can add the library separately from [NuGet](https://www.nuget.org/packages/GroupDocs.Classification) or [GroupDocs Releases](https://releases.groupdocs.com/classification/net/).  \n\n"
        "## What’s new in this release\n\n"
        "The following products were updated in this version:\n\n"
        "* GroupDocs.Conversion for .NET (25.7 → 25.8)\n"
        "* GroupDocs.Viewer for .NET (25.7 → 25.8)\n"
        "* GroupDocs.Comparison for .NET (25.7 → 25.8)\n"
        "* GroupDocs.Metadata for .NET (25.7 → 25.8)\n"
        "* GroupDocs.Parser for .NET (25.7 → 25.8)\n\n"
        "### Fixes\n\n"
        "| Issue | Product | Description |\n|-------|-----------|-------------|\n| **TOTALNET‑204** | Conversion | Fixed incorrect table formatting when converting HTML → PDF. |\n| **TOTALNET‑287** | Annotation | Resolved missing localized string error: “CONSTRUCTOR.WITH.PARAMETERS.STARTED” key does not exist. |\n| **TOTALNET‑298** | Viewer | Fixed a null‑reference exception that occurred on diagram rendering. |\n\n"
        "No new public‑API features or enhancements were introduced in this release.\n\n"
        "## How to get the update\n\n"
        "### NuGet\n\n"
        "Upgrade the **GroupDocs.Total** package (or the .NET Framework‑specific package) to the latest version:  \n\n"
        "  * [.NET 6](https://www.nuget.org/packages/GroupDocs.Total)  \n"
        "  * [.NET Framework 4.6.2+](https://www.nuget.org/packages/GroupDocs.Total.NETFramework)\n\n"
        "### Direct download\n\n"
        "Grab the compiled assemblies for both .NET 6 and .NET Framework from the [GroupDocs.Total for .NET {version} download page](https://releases.groupdocs.com/total/net/new-releases/groupdocs.total-for-.net-{version}/).\n\n"
        "## Resources\n\n"
        "- [Full release notes]({release_notes_url})\n"
        "- [Documentation](https://docs.groupdocs.com/total/net/)\n"
        "- [Free Support Forum](https://forum.groupdocs.com/c/total/8)\n\n"
        "---\n"
    )

    example_template = total_example_template if "Total" in inputs.product else viewer_example_template

    prompt = (
        f"You are drafting a public release blog post for {inputs.product} v{inputs.version}.\n"
        f"Title: {inputs.title}\n\n"
        "Use the following release notes HTML (from the main content of the page) as the source of truth. "
        "Extract the key changes, list new features, improvements, and fixed issues, and produce a clear, reader-friendly "
        "blog draft in Markdown. Follow the tone and structure of the example template below, "
        "adapting names, links, and counts to match this release. Keep wording precise and technical, not marketing-heavy.\n\n"
        "<example_template>\n"
        f"{example_template}\n"
        "</example_template>\n\n"
        "Use the provided front matter below as the exact header (YAML) for the post. Generate ONLY the body content after it.\n\n"
        "<front_matter>\n"
        f"{build_front_matter_yaml(inputs)}\n"
        "</front_matter>\n\n"
        "When generating links, prefer those found in the release notes. If unavailable, omit.\n\n"
        "<release_notes>\n"
        f"{release_notes_html}\n"
        "</release_notes>\n"
    )
    logging.debug("Built LLM prompt length: %d", len(prompt))
    return prompt


def generate_draft_with_llm(prompt: str) -> str:
    logging.info("Calling LLM to generate draft body...")
    api_key = os.getenv("PROFESSIONALIZE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing PROFESSIONALIZE_API_KEY environment variable")

    api_url = os.getenv("PROFESSIONALIZE_API_URL")
    if not api_url:
        raise RuntimeError("Missing PROFESSIONALIZE_API_URL environment variable")

    client = OpenAI(api_key=api_key, base_url=api_url)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional tech blog writer. "
                "Write articles for Hugo in Markdown"
                "Keep the content accurate and concise."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    # For Professionalize
    response = client.chat.completions.create(model="recommended", messages=messages)
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
        # Should contain at least one heading or list section to ensure structure
        has_heading = bool(re.search(r"^##\s+.+", md, flags=re.MULTILINE))
        has_list = bool(re.search(r"^\s*[-*+]\s+.+", md, flags=re.MULTILINE))
        if not (has_heading or has_list):
            raise ValueError("Generated content lacks headings or lists expected in a release post.")
        # Should not contain YAML front matter blocks
        if re.search(r"^---[\s\S]*?\n---\s*$", md, flags=re.MULTILINE):
            raise ValueError("Generated content unexpectedly includes YAML front matter.")

    cleaned = _strip_possible_front_matter_if_present(content)
    try:
        _validate_markdown_body(cleaned)
        logging.debug("LLM markdown validation succeeded")
    except Exception as e:
        logging.error("LLM markdown validation failed: %s", e)
        raise

    return content


def review_full_post_with_llm(full_post_markdown: str) -> str:
    logging.info("Reviewing full post with LLM for improvement suggestions")
    api_key = os.getenv("PROFESSIONALIZE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing PROFESSIONALIZE_API_KEY environment variable")

    api_url = os.getenv("PROFESSIONALIZE_API_URL")
    if not api_url:
        raise RuntimeError("Missing PROFESSIONALIZE_API_URL environment variable")

    client = OpenAI(api_key=api_key, base_url=api_url)

    review_instructions = (
        "Review the blog post and provide concise, actionable suggestions without rewriting the entire post. Focus on: "
        "structure and clarity, correctness and formatting."
        "Keep it short and output suggestions a list of bullet points."
    )

    messages = [
        {"role": "system", "content": review_instructions},
        {
            "role": "user",
            "content": (
                "Here is the full post. Suggest improvements as a checklist and short notes, "
                "organized under two sections: Summary, Suggestions.\n\n"
                "<post>\n"
                f"{full_post_markdown}\n"
                "</post>\n"
            ),
        },
    ]

    response = client.chat.completions.create(model="recommended", messages=messages)
    suggestions = response.choices[0].message.content.strip()
    logging.debug("LLM review suggestions length: %d", len(suggestions))
    return suggestions


def refine_front_matter_with_llm(full_post_markdown: str) -> Dict[str, Any]:
    logging.debug("Improving front matter with LLM")
    api_key = os.getenv("PROFESSIONALIZE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing PROFESSIONALIZE_API_KEY environment variable")

    api_url = os.getenv("PROFESSIONALIZE_API_URL")
    if not api_url:
        raise RuntimeError("Missing PROFESSIONALIZE_API_URL environment variable")

    client = OpenAI(api_key=api_key, base_url=api_url)

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

    response = client.chat.completions.create(model="recommended", messages=messages)
    raw = response.choices[0].message.content.strip()
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
    def rep_line(key: str, value: str) -> str:
        def _escape_double_quotes(s: str) -> str:
            return s.replace('"', '\\"')
        pattern = rf"^(" + re.escape(key) + r":\s*)\"[^\"]*\"\s*$"
        return re.sub(
            pattern,
            lambda m: m.group(1) + f"\"{_escape_double_quotes(value)}\"",
            fm,
            flags=re.MULTILINE,
        )

    fm_updated = fm
    fm_updated = rep_line("seoTitle", improvements.get("seoTitle", ""))
    fm_updated = rep_line("description", improvements.get("description", ""))
    fm_updated = rep_line("summary", improvements.get("summary", ""))

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

        # Generate blog body via LLM
        body_md = generate_draft_with_llm(prompt)

        # If the model returned front matter (despite instructions), strip it
        def _strip_front_matter(text: str) -> str:
            t = text.lstrip("\ufeff\n\r ")
            if t.startswith("---"):
                # remove first front matter block
                m = re.search(r"^---[\s\S]*?\n---\s*\n?", t)
                if m:
                    return t[m.end():]
            return t

        before_len = len(body_md)
        body_md = _strip_front_matter(body_md).lstrip()
        logging.debug("Post-processed body: before=%d, after=%d", before_len, len(body_md))

        final_md = f"{front_matter}\n\n{body_md}\n"

        # Improve front matter fields using LLM (seoTitle, description, summary, tags, cover alt/caption)
        logging.info("Improving front matter fields using LLM...")
        try:
            fm_text, body_text = split_front_matter_blocks(final_md)
            improvements = refine_front_matter_with_llm(final_md)
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

        # Review the complete post and print suggestions (optional)
        if inputs.review_enabled:
            suggestions = review_full_post_with_llm(final_md)
            print("\nReviewer suggestions:\n")
            print(suggestions)
        return 0
    except Exception as exc:
        logging.error("Error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
