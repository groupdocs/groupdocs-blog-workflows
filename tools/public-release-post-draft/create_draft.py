import argparse
import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, timezone
import os
import logging

import requests
from bs4 import BeautifulSoup
from openai import OpenAI


@dataclass
class DraftInputs:
    product: str
    version: str
    title: str
    release_notes_url: str


def parse_args(argv: Optional[list[str]] = None) -> DraftInputs:
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

    ns = parser.parse_args(argv)

    url = ns.release_notes.strip()
    # Allow a leading '@' prefix (e.g. copied from chat)
    url = url[1:] if url.startswith("@") else url

    inputs = DraftInputs(product=ns.product, version=ns.version, title=ns.title, release_notes_url=url)
    logging.info("Parsed inputs: product='%s', version='%s', title='%s'", inputs.product, inputs.version, inputs.title)
    logging.info("Release notes URL: %s", inputs.release_notes_url)
    return inputs


def fetch_release_notes_main_section(url: str) -> str:
    logging.info("Fetching release notes from: %s", url)
    headers = {
        "User-Agent": "groupdocs-blog-workflows/1.0 (+https://blog.groupdocs.com)"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    logging.info("Fetched release notes: status=%s, bytes=%d", resp.status_code, len(resp.text))

    soup = BeautifulSoup(resp.text, "html.parser")
    main_section = soup.find("section", attrs={"role": "main"})
    if not main_section:
        # Fallback: try main tag or primary content container
        logging.info("<section role='main'> not found, trying fallbacks <main> or div[role='main']")
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
    logging.info("Extracted main section HTML length: %d", len(inner))
    return inner


def _parse_month_year_from_title(title: str) -> Tuple[Optional[str], Optional[int]]:
    logging.info("Parsing month/year from title: %s", title)
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
    logging.info("Parsed month/year: %s %s", norm_month, year)
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


def build_front_matter(inputs: DraftInputs) -> str:
    # Derive components
    month_name, year = _parse_month_year_from_title(inputs.title)
    month_year = f"{month_name} {year}" if month_name and year else inputs.title
    family_slug, product_short, platform_label = _extract_family_and_platform(inputs.product)
    platform_slug = _platform_to_slug(platform_label)
    version_slug = _version_to_slug(inputs.version)
    name_slug = f"groupdocs-{family_slug}-for-{platform_slug}-{version_slug}"
    url = f"/{family_slug}/{name_slug}/"
    logging.info("Front matter slugs: family=%s, platform=%s, version=%s", family_slug, platform_slug, version_slug)
    logging.info("Post URL: %s", url)

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
    fm_lines = [
        "---",
        f"title: \"{title}\"",
        f"seoTitle: \"{seo_title}\"",
        f"description: \"{description}\"",
        f"date: {rfc1123}",
        "draft: false",
        f"url: {url}",
        "author: \"GroupDocs Team\"",
        f"summary: \"{summary}\"",
        f"tags: ['{tags[0]}', '{tags[1]}'{'' if len(tags) == 2 else ", '" + "', '".join(tags[2:]) + "'"}]",
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
    logging.info("Built front matter length: %d", len(fm))
    return fm


def build_llm_prompt(inputs: DraftInputs, release_notes_html: str) -> str:
    # Provide the model with clear structure and a concrete example to emulate.
    example_template = (
        "We’re happy to announce the major release of **{product} {version}**, available as of **{month_year}**. "
        "This major release delivers two new features with public API changes, one enhancement and 4 fixed bug.\n\n"
        "## New features\n\n"
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
        "## Learn more\n\n"
        "* [Full Release Notes]({release_notes_url})  \n"
        "* [Documentation](https://docs.groupdocs.com/viewer/net/)  \n"
        "* [GroupDocs.Viewer Free Support Forum](https://forum.groupdocs.com/c/viewer/9)  \n\n"
        "---\n"
    )

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
        f"{build_front_matter(inputs)}\n"
        "</front_matter>\n\n"
        "When generating links, prefer those found in the release notes. If unavailable, omit.\n\n"
        "<release_notes>\n"
        f"{release_notes_html}\n"
        "</release_notes>\n"
    )
    logging.info("Built LLM prompt length: %d", len(prompt))
    return prompt


def call_llm_generate_draft(prompt: str) -> str:
    logging.info("Calling LLM to generate draft body")
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
    logging.info("LLM response length: %d", len(content))
    return content


def main(argv: Optional[list[str]] = None) -> int:
    try:
        # Basic logging setup; respect LOG_LEVEL if set, default to INFO
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="%(levelname)s %(message)s")
        logging.info("Starting draft generation pipeline")
        inputs = parse_args(argv)
        notes_html = fetch_release_notes_main_section(inputs.release_notes_url)
        front_matter = build_front_matter(inputs)
        prompt = build_llm_prompt(inputs, notes_html)

        # Generate blog body via LLM
        body_md = call_llm_generate_draft(prompt)

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
        logging.info("Post-processed body: before=%d, after=%d", before_len, len(body_md))

        final_md = f"{front_matter}\n\n{body_md}\n"

        # Save to output/index.md within tool directory
        out_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        logging.info("Saved final markdown: %s (chars=%d)", out_path, len(final_md))
        return 0
    except Exception as exc:
        logging.error("Error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


