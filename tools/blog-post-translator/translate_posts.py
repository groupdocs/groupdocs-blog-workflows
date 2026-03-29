#!/usr/bin/env python3
"""
Blog Post Translator

Reads translation status report and translates missing blog posts using LLM.
"""

import os
import sys
import json
import yaml
import argparse
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI


LANG_NAMES = {
    'ar': 'Arabic', 'cs': 'Czech', 'de': 'German', 'es': 'Spanish',
    'fa': 'Persian/Farsi', 'fr': 'French', 'he': 'Hebrew', 'id': 'Indonesian',
    'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean', 'nl': 'Dutch',
    'pl': 'Polish', 'pt': 'Portuguese', 'ru': 'Russian', 'th': 'Thai',
    'tr': 'Turkish', 'uk': 'Ukrainian', 'vi': 'Vietnamese',
    'zh': 'Chinese (Simplified)', 'zh-hant': 'Chinese (Traditional)',
}

# Metrics tracking for token usage, API calls, and item counts
_metrics = {"token_usage": 0, "api_calls_count": 0, "items_translated": 0, "items_failed": 0}


def _track_usage(response):
    """Extract and accumulate token usage from an API response."""
    _metrics["api_calls_count"] += 1
    if hasattr(response, 'usage') and response.usage:
        _metrics["token_usage"] += getattr(response.usage, 'total_tokens', 0)


def create_client() -> OpenAI:
    """Create OpenAI client from environment variables."""
    api_key = os.getenv("PROFESSIONALIZE_API_KEY")
    base_url = os.getenv("PROFESSIONALIZE_API_URL", "https://llm.professionalize.com/v1")
    if not api_key:
        raise SystemExit("Missing environment variable: PROFESSIONALIZE_API_KEY")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_model_name() -> str:
    """Get model name from environment variable."""
    return os.getenv("PROFESSIONALIZE_MODEL_NAME", "recommended")


def get_reviewer_model() -> Optional[str]:
    """Get reviewer model name. Returns None if review is disabled."""
    return os.getenv("PROFESSIONALIZE_REVIEWER_MODEL", None)


def load_translation_report(report_path: str) -> Dict:
    """Load translation status report."""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Report file not found: {report_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse report file: {e}")
        sys.exit(1)


def read_post_file(post_path: str) -> Optional[str]:
    """Read blog post markdown file."""
    post_file = Path(post_path) / 'index.md'
    
    if not post_file.exists():
        print(f"Warning: Post file not found: {post_file}")
        return None
    
    try:
        with open(post_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading post file {post_file}: {e}")
        return None


def parse_front_matter(content: str):
    """
    Parse front-matter from markdown content.
    
    Returns:
        Tuple of (front_matter_dict, content_body)
    """
    if not content.startswith('---'):
        return None, content
    
    # Find the end of front-matter
    end_marker = content.find('\n---', 4)  # Skip first ---
    if end_marker == -1:
        return None, content
    
    front_matter_text = content[4:end_marker]  # Skip first ---\n
    content_body = content[end_marker + 5:].lstrip()  # Skip \n---\n
    
    try:
        front_matter = yaml.safe_load(front_matter_text)
        return front_matter, content_body
    except Exception as e:
        print(f"Warning: Failed to parse front-matter: {e}")
        return None, content


def _strip_prompt_leakage(text: str, target_lang_name: str) -> str:
    """
    Strip prompt instructions that the model may have echoed at the start of its response.

    Detects patterns like "Translate to Portuguese.\n\nRules:\n- ..." and removes
    everything up to and including the glossary block, leaving only the actual translation.
    """
    # Pattern: "Translate to <language>" followed by rules/glossary block
    # The glossary ends with "Free Support Forum\n"
    leakage_pattern = re.compile(
        r'^Translate\s+to\s+.+?\.\s*\n'   # "Translate to Portuguese."
        r'(?:.*?\n)*?'                      # rules lines
        r'.*?Free Support Forum\s*\n'       # end of glossary
        r'\s*',                             # trailing whitespace
        re.IGNORECASE | re.DOTALL
    )
    cleaned = leakage_pattern.sub('', text, count=1)

    # Also catch partial leakage: just "Translate to <lang>." at the start
    if cleaned.startswith(f"Translate to {target_lang_name}"):
        first_newline = cleaned.find('\n')
        if first_newline > 0:
            cleaned = cleaned[first_newline:].lstrip()

    return cleaned


def _extract_shortcode_blocks(text: str):
    """
    Extract paired shortcode blocks (e.g. {{< fixedheight >}}...{{< /fixedheight >}})
    and replace them with placeholders.

    These blocks contain non-translatable content (code samples, raw markdown)
    that should be preserved verbatim. Extracting them prevents the LLM from
    truncating or translating the content.

    Returns:
        Tuple of (text_with_placeholders, list_of_extracted_blocks)
    """
    # Match paired shortcodes: {{< name ... >}} ... {{< /name >}}
    pattern = r'(\{\{<\s*(\w[\w-]*)\s[^>]*>}}[\s\S]*?\{\{<\s*/\s*\2\s*>}})'
    blocks = []

    def _replacer(match):
        blocks.append(match.group(0))
        idx = len(blocks) - 1
        return f'SHORTCODE_BLOCK_{idx}_PRESERVED'

    cleaned = re.sub(pattern, _replacer, text)
    return cleaned, blocks


def _restore_shortcode_blocks(text: str, blocks: list) -> str:
    """Restore extracted shortcode blocks from placeholders."""
    for idx, block in enumerate(blocks):
        placeholder = f'SHORTCODE_BLOCK_{idx}_PRESERVED'
        text = text.replace(placeholder, block)
    return text


def _fix_shortcodes(source_body: str, translated_body: str) -> str:
    """
    Auto-fix shortcode issues in translated text.

    Removes closing shortcode tags (e.g. {{< /iframe >}}) that the LLM
    may have invented but that do not exist in the source text.
    """
    closing_tag_re = r'\{\{<\s*/\s*(\w[\w-]*)\s*>}}'

    source_closing_names = set(re.findall(closing_tag_re, source_body))

    def _remove_if_spurious(match):
        name = match.group(1)
        if name not in source_closing_names:
            return ''
        return match.group(0)

    fixed = re.sub(closing_tag_re, _remove_if_spurious, translated_body)
    if fixed != translated_body:
        removed = set(re.findall(closing_tag_re, translated_body)) - source_closing_names
        for name in sorted(removed):
            print(f"    Auto-fixed: removed spurious {{{{< /{name} >}}}}")
    return fixed


def translate_text(client: OpenAI, model: str, text: str, target_lang: str, context: str = "") -> Optional[str]:
    """
    Translate text using LLM.
    
    Args:
        client: OpenAI client
        model: Model name
        text: Text to translate
        target_lang: Target language code
        context: Additional context for translation
    
    Returns:
        Translated text or None if translation fails
    """
    target_lang_name = LANG_NAMES.get(target_lang, target_lang)
    
    prompt = (
        f"Translate to {target_lang_name}. {context}\n"
        "\n"
        "Rules:\n"
        "- Output the COMPLETE translation. Every section, table, and link must appear.\n"
        "- Preserve markdown formatting exactly (##, |, **, [](), ```).\n"
        "- Do NOT translate: URLs, code blocks, version numbers, package names.\n"
        "- Copy Hugo shortcodes EXACTLY as they appear, including opening AND closing tags "
        "(e.g. {{< figure ... >}}, {{< fixedheight ... >}}...{{< /fixedheight >}}). "
        "Do NOT add closing tags ({{< /name >}}) that are not in the original.\n"
        "- Copy link reference definitions verbatim: [N]: https://...\n"
        "\n"
        "Glossary — keep these terms in English:\n"
        "GroupDocs.Total, GroupDocs.Watermark, GroupDocs.Annotation, GroupDocs.Assembly, "
        "GroupDocs.Comparison, GroupDocs.Conversion, GroupDocs.Editor, GroupDocs.Merger, "
        "GroupDocs.Metadata, GroupDocs.Parser, GroupDocs.Redaction, GroupDocs.Search, "
        "GroupDocs.Signature, GroupDocs.Viewer, GroupDocs.Markdown, "
        ".NET, .NET Framework, NuGet, C#, net6.0, Free Support Forum\n"
        "\n"
        f"{text}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Translate to {target_lang_name}. Preserve all markdown and code. Complete translation only, no commentary."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        _track_usage(response)
        result = response.choices[0].message.content.strip()
        result = _strip_prompt_leakage(result, target_lang_name)
        return result
    except Exception as e:
        print(f"Error translating text: {e}")
        return None


def update_url_for_language(url: str, lang_code: str) -> str:
    """
    Update URL to include language prefix.
    
    Args:
        url: Original URL (e.g., "/comparison/groupdocs-comparison-for-net-25-8/")
        lang_code: Language code (e.g., "ar")
    
    Returns:
        URL with language prefix (e.g., "/ar/comparison/groupdocs-comparison-for-net-25-8/")
    """
    if lang_code == 'en':
        return url
    
    # Remove leading slash if present, add language prefix
    url_clean = url.lstrip('/')
    return f"/{lang_code}/{url_clean}"


# ---------------------------------------------------------------------------
# Structural checks (fast, no LLM needed)
# ---------------------------------------------------------------------------
def structural_check(source_body: str, translated_body: str) -> List[str]:
    """
    Run programmatic structural checks on a translation.
    Returns a list of issue names (empty = all good).
    """
    issues = []

    # Code blocks
    src_cb = len(re.findall(r'```', source_body))
    tr_cb = len(re.findall(r'```', translated_body))
    if src_cb > 0 and abs(src_cb - tr_cb) > 2:
        issues.append("code_blocks_mismatch")

    # Markdown headers
    src_h = len(re.findall(r'^#{1,6}\s+', source_body, re.MULTILINE))
    tr_h = len(re.findall(r'^#{1,6}\s+', translated_body, re.MULTILINE))
    if src_h > 0 and abs(src_h - tr_h) > 2:
        issues.append("headers_mismatch")

    # Hugo shortcodes preserved (name-based check, handles multi-line shortcodes)
    sc_name_re = r'\{\{<\s*(/?[\w][\w-]*)'
    src_sc_names = re.findall(sc_name_re, source_body)
    tr_sc_names = re.findall(sc_name_re, translated_body)
    if src_sc_names:
        for name in set(src_sc_names):
            src_count = src_sc_names.count(name)
            tr_count = tr_sc_names.count(name)
            if tr_count < src_count:
                issues.append(f"shortcodes_missing({name})")

    # Link reference definitions preserved
    src_refs = set(re.findall(r'^\[\d+\]:\s*https?://\S+', source_body, re.MULTILINE))
    if src_refs:
        missing = [ref for ref in src_refs if ref not in translated_body]
        if missing:
            issues.append(f"link_refs_missing({len(missing)})")

    # Length ratio (catch severe truncation)
    if len(source_body) > 500:
        ratio = len(translated_body) / len(source_body)
        if ratio < 0.3:
            issues.append("likely_truncated")

    # Prompt leakage detection
    if re.search(r'^Translate\s+to\s+\w+', translated_body, re.MULTILINE):
        issues.append("prompt_leakage")
    if 'Free Support Forum' in translated_body and 'Glossary' in translated_body:
        issues.append("prompt_leakage")

    # Product names preserved
    names = set(re.findall(r'GroupDocs\.\w+', source_body))
    if names:
        missing = [n for n in names if n not in translated_body]
        if len(missing) > len(names) * 0.5:
            issues.append("product_names_missing")

    return issues


# ---------------------------------------------------------------------------
# LLM review (cross-model quality check)
# ---------------------------------------------------------------------------
REVIEW_PROMPT = """\
You are reviewing a translation from English to {target_language}.

Check for these issues:
1. Are markdown headers (##) translated or left in English?
2. Are Hugo shortcodes ({{{{< figure ... >}}}}) preserved exactly?
3. Are code blocks preserved without modification?
4. Are product names (GroupDocs.*, .NET, NuGet) kept in English?
5. Is the translation complete or truncated?

If the translation is GOOD, respond with exactly: PASS
If there are issues, respond with: FAIL followed by a brief list of specific problems found.

ORIGINAL (English, first 2000 chars):
{source}

TRANSLATION ({target_language}, first 2000 chars):
{translation}"""


def review_translation(client: OpenAI, reviewer_model: str,
                       source_body: str, translated_body: str,
                       lang_code: str) -> Optional[str]:
    """
    Use a separate model to review translation quality.
    Returns None if PASS, or a string with issues if FAIL.
    """
    target_lang = LANG_NAMES.get(lang_code, lang_code)
    prompt = REVIEW_PROMPT.format(
        target_language=target_lang,
        source=source_body[:2000],
        translation=translated_body[:2000],
    )
    try:
        response = client.chat.completions.create(
            model=reviewer_model,
            messages=[{"role": "user", "content": prompt}],
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
        print(f"Warning: Review call failed ({e}), skipping review")
        return None


def translate_front_matter(client: OpenAI, model: str, front_matter: Dict, lang_code: str) -> Dict:
    """
    Translate front-matter fields as a single JSON batch (reduces API calls).

    Args:
        client: OpenAI client
        model: Model name
        front_matter: Original front-matter dictionary
        lang_code: Target language code

    Returns:
        Translated front-matter dictionary
    """
    target_lang_name = LANG_NAMES.get(lang_code, lang_code)

    translated = front_matter.copy()

    # Collect all translatable fields into a JSON batch
    fields = {}
    for key in ['title', 'seoTitle', 'description', 'summary']:
        if key in translated and translated[key]:
            fields[key] = str(translated[key])
    if 'cover' in translated and isinstance(translated['cover'], dict):
        for key in ['alt', 'caption']:
            if key in translated['cover'] and translated['cover'][key]:
                fields[f'cover.{key}'] = str(translated['cover'][key])

    if fields:
        prompt = (
            f"Translate these blog post metadata values to {target_lang_name}.\n"
            f"Keep product names (GroupDocs.*, .NET, NuGet, C#) and version numbers in English.\n"
            f"Return ONLY a valid JSON object with the same keys. No explanation, no code fences.\n"
            f"\n"
            f"{json.dumps(fields, ensure_ascii=False, indent=2)}"
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"Translate to {target_lang_name}. Preserve all markdown and code. Complete translation only, no commentary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            _track_usage(response)
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            raw = re.sub(r'```(?:json)?\s*', '', raw).strip()
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                batch_translated = json.loads(json_match.group())
                for key in ['title', 'seoTitle', 'description', 'summary']:
                    if key in batch_translated:
                        translated[key] = batch_translated[key]
                if 'cover' in translated and isinstance(translated['cover'], dict):
                    for key in ['alt', 'caption']:
                        dotkey = f'cover.{key}'
                        if dotkey in batch_translated:
                            translated['cover'][key] = batch_translated[dotkey]
        except Exception as e:
            print(f"Warning: Batch front-matter translation failed ({e}), falling back to individual fields")
            # Fallback: translate fields individually
            for field in ['title', 'seoTitle', 'description', 'summary']:
                if field in translated and translated[field]:
                    result = translate_text(client, model, translated[field], lang_code,
                                            context=f"This is a {field} field for a technical blog post.")
                    if result:
                        translated[field] = result

    # Update URL for language
    if 'url' in translated:
        translated['url'] = update_url_for_language(translated['url'], lang_code)

    return translated


def verify_translation(
    post_path: str, 
    lang_code: str, 
    original_content: str = None,
    min_content_length: int = 100
) -> bool:
    """
    Verify that a translation was successful by checking if the file exists, has content,
    and key parts (front matter and headers) are actually translated.
    
    Args:
        post_path: Path to post directory
        lang_code: Language code
        original_content: Optional original English content for comparison
        min_content_length: Minimum content length to consider translation valid
    
    Returns:
        True if translation file exists, has sufficient content, and key parts are translated
    """
    post_dir = Path(post_path)
    output_file = post_dir / f'index.{lang_code}.md'
    
    if not output_file.exists():
        return False
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            translated_content = f.read()
        
        # Check if file has minimum content length
        if len(translated_content.strip()) < min_content_length:
            return False
        
        # Check if file has front matter (should start with ---)
        if not translated_content.strip().startswith('---'):
            return False
        
        # Parse translated front matter and content
        translated_fm, translated_body = parse_front_matter(translated_content)
        if not translated_fm:
            return False
        
        # Check if file has some actual content after front matter
        if len(translated_body.strip()) < 50:
            return False
        
        # If original content is provided, verify key parts are translated
        if original_content:
            original_fm, original_body = parse_front_matter(original_content)
            
            if original_fm:
                # Check front matter fields are translated
                fields_to_check = ['title', 'description', 'summary']
                front_matter_translated = False
                
                for field in fields_to_check:
                    if field in translated_fm and field in original_fm:
                        translated_value = str(translated_fm[field]).strip().lower()
                        original_value = str(original_fm[field]).strip().lower()
                        
                        # If values are different (and not just URL changes), consider translated
                        if translated_value != original_value and len(translated_value) > 0:
                            # Check if it's not just a URL change
                            if not (translated_value.startswith('/') and original_value.startswith('/')):
                                front_matter_translated = True
                                break
                
                # Check headers are translated
                # Extract headers from both versions (markdown headers: # ## ###)
                translated_headers = re.findall(r'^#{1,6}\s+(.+)$', translated_body, re.MULTILINE)
                original_headers = re.findall(r'^#{1,6}\s+(.+)$', original_body, re.MULTILINE)
                
                headers_translated = False
                if translated_headers and original_headers:
                    # Compare first few headers (up to 3)
                    min_headers = min(len(translated_headers), len(original_headers), 3)
                    if min_headers > 0:
                        different_count = 0
                        for i in range(min_headers):
                            trans_header = translated_headers[i].strip().lower()
                            orig_header = original_headers[i].strip().lower()
                            if trans_header != orig_header:
                                different_count += 1
                        
                        # At least one header should be different (translated)
                        if different_count > 0:
                            headers_translated = True
                
                # Verification logic:
                # 1. If front matter OR headers are translated, consider it successful
                if front_matter_translated or headers_translated:
                    return True
                
                # 2. If there are headers in the original but none were translated, fail
                if len(original_headers) > 0 and not headers_translated:
                    return False
                
                # 3. If no headers exist and front matter not translated, be lenient but log warning
                # (some posts might have very similar front matter or no translatable content)
                if len(original_headers) == 0 and not front_matter_translated:
                    print(f"Warning: Could not verify translation quality for {post_path} ({lang_code}) - front matter appears unchanged")
                    # Still return True if file structure is valid (might be edge case)
                    return True
                
                # 4. Default: fail if we can't verify translation
                return False
        
        # If no original content provided, just check file structure
        return True
        
    except Exception as e:
        print(f"Error verifying translation file {output_file}: {e}")
        return False


def save_translated_post(post_path: str, lang_code: str, front_matter: Dict, content: str):
    """
    Save translated post to file.
    
    Args:
        post_path: Path to post directory
        lang_code: Language code
        front_matter: Translated front-matter dictionary
        content: Translated content body
    """
    post_dir = Path(post_path)
    output_file = post_dir / f'index.{lang_code}.md'
    
    # Convert front-matter to YAML
    front_matter_yaml = yaml.dump(
        front_matter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )
    
    # Combine front-matter and content
    full_content = f"---\n{front_matter_yaml}---\n\n{content}"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        return True
    except Exception as e:
        print(f"Error saving translated post to {output_file}: {e}")
        return False


def translate_post(
    client: OpenAI,
    model: str,
    post_path: str,
    lang_code: str,
    verbose: bool = False,
    max_retries: int = 3,
    reviewer_model: Optional[str] = None,
) -> bool:
    """
    Translate a single blog post to target language with structural checks
    and optional cross-model review.

    Flow per attempt:
      1. Translate front-matter (batch JSON) + body
      2. Run structural checks (free, no LLM)
      3. If reviewer_model set, run LLM review (cross-model)
      4. If issues found, retry with feedback included in context

    Args:
        client: OpenAI client
        model: Model name for translation
        post_path: Path to post directory
        lang_code: Target language code
        verbose: Enable verbose output
        max_retries: Maximum number of retry attempts (default: 3)
        reviewer_model: Model name for quality review (None = skip review)

    Returns:
        True if translation succeeded, False otherwise
    """
    if verbose:
        print(f"Translating {post_path} to {lang_code}...")

    # Read English post
    original_content = read_post_file(post_path)
    if not original_content:
        return False

    # Parse front-matter and content
    front_matter, content_body = parse_front_matter(original_content)
    if not front_matter:
        print(f"Warning: Could not parse front-matter for {post_path}")
        return False

    # Extract paired shortcode blocks (e.g. fixedheight) before translation
    # so the LLM doesn't need to reproduce their (potentially huge) content
    translatable_body, shortcode_blocks = _extract_shortcode_blocks(content_body)
    if shortcode_blocks and verbose:
        print(f"    Extracted {len(shortcode_blocks)} shortcode block(s) for preservation")

    feedback_context = ""  # Accumulated feedback from failed attempts

    # Try translation with retries
    for attempt in range(1, max_retries + 1):
        try:
            # Translate front-matter
            translated_front_matter = translate_front_matter(client, model, front_matter, lang_code)

            # Translate content body (include feedback from prior attempts)
            translated_content = translate_text(
                client, model, translatable_body, lang_code,
                context=feedback_context
            )

            if not translated_content:
                if attempt < max_retries:
                    print(f"Warning: Translation attempt {attempt} failed for {post_path} ({lang_code}), retrying...")
                    time.sleep(2)
                    continue
                else:
                    print(f"Error: Failed to translate content for {post_path} ({lang_code}) after {max_retries} attempts")
                    return False

            # --- Step 1b: Restore preserved shortcode blocks ---
            if shortcode_blocks:
                translated_content = _restore_shortcode_blocks(translated_content, shortcode_blocks)

            # --- Step 1c: Auto-fix shortcode issues ---
            translated_content = _fix_shortcodes(content_body, translated_content)

            # --- Step 2: Structural checks (fast, no LLM) ---
            struct_issues = structural_check(content_body, translated_content)
            if struct_issues:
                issues_str = ", ".join(struct_issues)
                if attempt < max_retries:
                    if verbose:
                        print(f"    Structural issues (attempt {attempt}): {issues_str}")
                    feedback_context = (
                        f"IMPORTANT: Your previous translation had these structural issues: {issues_str}. "
                        f"Fix them in this attempt."
                    )
                    time.sleep(1)
                    continue
                else:
                    # On final attempt, fail for shortcode issues (cause Hugo build errors)
                    shortcode_issues = [i for i in struct_issues if 'shortcode' in i]
                    if shortcode_issues:
                        print(f"Error: Shortcode issues persist after {max_retries} attempts "
                              f"for {post_path} ({lang_code}): {', '.join(shortcode_issues)}")
                        return False
                    if verbose:
                        print(f"    Warning: minor structural issues on final attempt: {issues_str}")

            # --- Step 3: LLM review (cross-model, optional) ---
            if reviewer_model and attempt < max_retries:
                review_result = review_translation(
                    client, reviewer_model, content_body, translated_content, lang_code
                )
                if review_result:
                    if verbose:
                        print(f"    Review issues (attempt {attempt}): {review_result[:200]}")
                    feedback_context = (
                        f"IMPORTANT: A reviewer found these issues in your previous translation: "
                        f"{review_result[:500]}. Fix them in this attempt."
                    )
                    time.sleep(1)
                    continue
                elif verbose:
                    print(f"    Review: PASS")

            # Save translated post
            save_success = save_translated_post(post_path, lang_code, translated_front_matter, translated_content)
            if not save_success:
                if attempt < max_retries:
                    print(f"Warning: Failed to save translation attempt {attempt} for {post_path} ({lang_code}), retrying...")
                    time.sleep(1)
                    continue
                else:
                    print(f"Error: Failed to save translation for {post_path} ({lang_code}) after {max_retries} attempts")
                    return False

            # Verify translation was successful (including checking key parts are translated)
            if verify_translation(post_path, lang_code, original_content):
                if verbose:
                    if attempt > 1:
                        print(f"Successfully translated {post_path} to {lang_code} (attempt {attempt})")
                    else:
                        print(f"Successfully translated {post_path} to {lang_code}")
                return True
            else:
                if attempt < max_retries:
                    print(f"Warning: Translation verification failed for {post_path} ({lang_code}) attempt {attempt} - key parts may not be translated, retrying...")
                    # Remove the failed translation file before retrying
                    output_file = Path(post_path) / f'index.{lang_code}.md'
                    try:
                        if output_file.exists():
                            output_file.unlink()
                    except Exception:
                        pass
                    feedback_context = "IMPORTANT: Your previous translation left headers untranslated. Translate ALL headers."
                    time.sleep(2)
                    continue
                else:
                    print(f"Error: Translation verification failed for {post_path} ({lang_code}) after {max_retries} attempts - key parts may not be translated")
                    return False

        except Exception as e:
            if attempt < max_retries:
                print(f"Warning: Exception during translation attempt {attempt} for {post_path} ({lang_code}): {e}, retrying...")
                time.sleep(2)
                continue
            else:
                print(f"Error: Exception during translation for {post_path} ({lang_code}) after {max_retries} attempts: {e}")
                return False

    return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Translate blog posts using LLM based on translation status report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python translate_posts.py translation_status.json
  python translate_posts.py translation_status.json --lang ar
  python translate_posts.py translation_status.json --post "content/Groupdocs.Blog/comparison/2025-09-01-groupdocs-comparison-for-net-25-8"
  python translate_posts.py translation_status.json --limit 5 --verbose
        """
    )
    
    parser.add_argument(
        'report',
        type=str,
        help='Path to translation status JSON report'
    )
    
    parser.add_argument(
        '--lang',
        type=str,
        default=None,
        help='Translate only to specific language code (e.g., ar, de, fr)'
    )
    
    parser.add_argument(
        '--post',
        type=str,
        default=None,
        help='Translate only specific post path'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of posts to translate'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - show what would be translated without actually translating'
    )
    
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts for failed translations (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Load report
    report = load_translation_report(args.report)
    posts = report.get('posts', [])
    
    if not posts:
        print("No posts with missing translations found in report.")
        sys.exit(0)
    
    print(f"Found {len(posts)} posts with missing translations")
    
    # Filter posts if --post specified
    if args.post:
        posts = [p for p in posts if args.post in p.get('path', '')]
        if not posts:
            print(f"No post found matching: {args.post}")
            sys.exit(1)
        print(f"Filtered to 1 post: {args.post}")
    
    # Limit posts if --limit specified
    if args.limit:
        posts = posts[:args.limit]
        print(f"Limited to {len(posts)} posts")
    
    if args.dry_run:
        print("\n=== DRY RUN MODE ===")
        for post in posts:
            print(f"\nPost: {post['path']}")
            langs_to_translate = [args.lang] if args.lang and args.lang in post['missing_languages'] else post['missing_languages']
            print(f"Missing languages: {', '.join(langs_to_translate)}")
        sys.exit(0)
    
    # Initialize LLM client
    try:
        client = create_client()
        model = get_model_name()
        reviewer_model = get_reviewer_model()
    except SystemExit as e:
        print(e)
        sys.exit(1)

    if reviewer_model:
        print(f"Reviewer model: {reviewer_model} (cross-model quality review enabled)")

    # Process each post
    total_translated = 0
    total_failed = 0

    for post_idx, post in enumerate(posts, 1):
        post_path = post['path']
        missing_langs = post['missing_languages']

        # Filter languages if --lang specified
        if args.lang:
            if args.lang not in missing_langs:
                if args.verbose:
                    print(f"Skipping {post_path} - {args.lang} not in missing languages")
                continue
            missing_langs = [args.lang]

        print(f"\n[{post_idx}/{len(posts)}] Processing: {post_path}")
        print(f"Missing languages: {', '.join(missing_langs)}")

        for lang_idx, lang_code in enumerate(missing_langs, 1):
            print(f"  [{lang_idx}/{len(missing_langs)}] Translating to {lang_code}...", end=' ', flush=True)

            success = translate_post(client, model, post_path, lang_code, args.verbose, args.retries, reviewer_model)
            
            if success:
                print("OK")
                total_translated += 1
            else:
                print("FAIL")
                total_failed += 1
    
    # Write metrics for workflow consumption
    _metrics["items_translated"] = total_translated
    _metrics["items_failed"] = total_failed
    try:
        with open('translation_metrics.json', 'w') as f:
            json.dump(_metrics, f)
    except Exception as e:
        print(f"Warning: Could not write metrics file: {e}", file=sys.stderr)

    # Summary
    print(f"\n{'='*80}")
    print("TRANSLATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total translations completed: {total_translated}")
    print(f"Total translations failed: {total_failed}")
    print(f"Token usage: {_metrics['token_usage']}")
    print(f"API calls: {_metrics['api_calls_count']}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()

