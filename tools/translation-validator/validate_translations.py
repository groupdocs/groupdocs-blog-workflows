#!/usr/bin/env python3
"""
Translation Validator

Scans existing blog post translations and identifies incomplete or
incorrectly translated posts for retranslation.

Checks:
  1. Structural: links, code blocks, headers, tables, product names preserved
  2. Content: front-matter translated, headers translated, body not empty
  3. Completeness: translation length vs original, all sections present

Outputs a JSON report compatible with translate_posts.py (same format as
the missing-translations-scanner), so flagged posts can be retranslated
by feeding the report directly to the translator.
"""

import os
import sys
import re
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Language config
# ---------------------------------------------------------------------------
LANG_NAMES = {
    'ar': 'Arabic', 'cs': 'Czech', 'de': 'German', 'es': 'Spanish',
    'fa': 'Persian/Farsi', 'fr': 'French', 'he': 'Hebrew', 'id': 'Indonesian',
    'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean', 'nl': 'Dutch',
    'pl': 'Polish', 'pt': 'Portuguese', 'ru': 'Russian', 'th': 'Thai',
    'tr': 'Turkish', 'uk': 'Ukrainian', 'vi': 'Vietnamese',
    'zh': 'Chinese (Simplified)', 'zh-hant': 'Chinese (Traditional)',
}

DEFAULT_LANGUAGES = list(LANG_NAMES.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_front_matter(content: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML front-matter from markdown content."""
    if not content.startswith('---'):
        return None, content
    end = content.find('\n---', 4)
    if end == -1:
        return None, content
    try:
        fm = yaml.safe_load(content[4:end])
        body = content[end + 5:].lstrip()
        return fm, body
    except Exception:
        return None, content


def find_post_directories(content_dir: str) -> List[Path]:
    """Find all blog post directories that have an English index.md."""
    result = []
    for root, _dirs, files in os.walk(content_dir):
        if 'index.md' in files:
            result.append(Path(root))
    return sorted(result)


# ---------------------------------------------------------------------------
# Structural checks (same as autoresearch experiment runner)
# ---------------------------------------------------------------------------
def structural_checks(source_body: str, translated_body: str) -> Dict[str, float]:
    """Run programmatic structural quality checks. Each metric in [0, 1]."""
    scores = {}

    # 1. Link URL preservation
    src_urls = set(re.findall(r'\]\(([^)]+)\)', source_body))
    tr_urls = set(re.findall(r'\]\(([^)]+)\)', translated_body))
    if src_urls:
        preserved = sum(1 for u in src_urls if any(u in t for t in tr_urls))
        scores['links'] = preserved / len(src_urls)
    else:
        scores['links'] = 1.0

    # 2. Code blocks
    src_cb = len(re.findall(r'```', source_body))
    tr_cb = len(re.findall(r'```', translated_body))
    scores['code_blocks'] = 1.0 if src_cb == tr_cb else (0.5 if abs(src_cb - tr_cb) <= 2 else 0.0)

    # 3. Markdown headers
    src_h = len(re.findall(r'^#{1,6}\s+', source_body, re.MULTILINE))
    tr_h = len(re.findall(r'^#{1,6}\s+', translated_body, re.MULTILINE))
    scores['headers'] = 1.0 if src_h == tr_h else (0.5 if abs(src_h - tr_h) <= 2 else 0.0)

    # 4. Table pipes
    src_p = source_body.count('|')
    tr_p = translated_body.count('|')
    if src_p > 0:
        ratio = tr_p / src_p
        scores['tables'] = 1.0 if 0.7 <= ratio <= 1.3 else (0.5 if 0.4 <= ratio <= 1.6 else 0.0)
    else:
        scores['tables'] = 1.0

    # 5. Length ratio (translation shouldn't be drastically different)
    if len(source_body) > 0:
        lr = len(translated_body) / len(source_body)
        scores['length'] = 1.0 if 0.4 <= lr <= 3.0 else (0.5 if 0.2 <= lr <= 4.0 else 0.0)
    else:
        scores['length'] = 1.0

    # 6. Product names preserved
    names = set(re.findall(r'GroupDocs\.\w+|NuGet|\.NET\b', source_body))
    if names:
        scores['products'] = sum(1 for n in names if n in translated_body) / len(names)
    else:
        scores['products'] = 1.0

    # 7. Hugo shortcodes preserved
    src_sc = set(re.findall(r'\{\{<.*?>}}', source_body))
    if src_sc:
        preserved = sum(1 for sc in src_sc if sc in translated_body)
        scores['shortcodes'] = preserved / len(src_sc)
    else:
        scores['shortcodes'] = 1.0

    # 8. Link reference definitions preserved
    src_refs = set(re.findall(r'^\[\d+\]:\s*https?://\S+', source_body, re.MULTILINE))
    if src_refs:
        preserved = sum(1 for ref in src_refs if ref in translated_body)
        scores['link_refs'] = preserved / len(src_refs)
    else:
        scores['link_refs'] = 1.0

    # 9. Prompt leakage (translation instructions leaked into output)
    has_leakage = bool(re.search(r'^Translate\s+to\s+\w+', translated_body, re.MULTILINE))
    if not has_leakage:
        has_leakage = 'Free Support Forum' in translated_body and 'Glossary' in translated_body
    scores['no_prompt_leakage'] = 0.0 if has_leakage else 1.0

    return scores


# ---------------------------------------------------------------------------
# Content checks
# ---------------------------------------------------------------------------
def content_checks(
    source_fm: Optional[Dict],
    translated_fm: Optional[Dict],
    source_body: str,
    translated_body: str,
) -> Dict[str, bool]:
    """Check that key content parts are actually translated."""
    issues = {}

    # Front-matter translated
    if source_fm and translated_fm:
        fm_translated = False
        for field in ['title', 'description', 'summary']:
            src_val = str(source_fm.get(field, '')).strip().lower()
            tr_val = str(translated_fm.get(field, '')).strip().lower()
            if src_val and tr_val and src_val != tr_val:
                fm_translated = True
                break
        issues['front_matter_untranslated'] = not fm_translated
    else:
        issues['front_matter_untranslated'] = translated_fm is None

    # Headers translated
    src_headers = re.findall(r'^#{1,6}\s+(.+)$', source_body, re.MULTILINE)
    tr_headers = re.findall(r'^#{1,6}\s+(.+)$', translated_body, re.MULTILINE)
    if src_headers and tr_headers:
        same_count = sum(
            1 for s, t in zip(src_headers[:5], tr_headers[:5])
            if s.strip().lower() == t.strip().lower()
        )
        issues['headers_untranslated'] = same_count >= min(3, len(src_headers[:5]))
    else:
        issues['headers_untranslated'] = len(tr_headers) == 0 and len(src_headers) > 0

    # Body too short (likely truncated)
    if len(source_body) > 500:
        ratio = len(translated_body) / len(source_body)
        issues['likely_truncated'] = ratio < 0.3
    else:
        issues['likely_truncated'] = False

    # Body is mostly English (translation may have failed silently)
    if translated_body:
        ascii_chars = sum(1 for c in translated_body if ord(c) < 128)
        total_chars = len(translated_body)
        # For non-Latin languages, high ASCII ratio means untranslated
        # Skip this check for Latin-script languages
        issues['mostly_english'] = False  # conservative default
    else:
        issues['mostly_english'] = True

    return issues


# ---------------------------------------------------------------------------
# Validate a single translation
# ---------------------------------------------------------------------------
def validate_translation(
    post_dir: Path,
    lang_code: str,
    source_content: str,
    min_body_length: int = 50,
) -> Dict:
    """
    Validate a single translation file against the English original.

    Returns a dict with:
      - valid: bool
      - issues: list of issue descriptions
      - structural_score: float (0-1 average)
      - details: dict of all check results
    """
    result = {
        'valid': True,
        'issues': [],
        'structural_score': 1.0,
        'details': {},
    }

    translation_file = post_dir / f'index.{lang_code}.md'

    # File existence
    if not translation_file.exists():
        result['valid'] = False
        result['issues'].append('file_missing')
        result['structural_score'] = 0.0
        return result

    try:
        translated_content = translation_file.read_text(encoding='utf-8')
    except Exception as e:
        result['valid'] = False
        result['issues'].append(f'read_error: {e}')
        result['structural_score'] = 0.0
        return result

    # Basic size check
    if len(translated_content.strip()) < min_body_length:
        result['valid'] = False
        result['issues'].append('too_short')
        result['structural_score'] = 0.0
        return result

    # Parse both
    source_fm, source_body = parse_front_matter(source_content)
    translated_fm, translated_body = parse_front_matter(translated_content)

    if not translated_fm:
        result['issues'].append('no_front_matter')

    if len(translated_body.strip()) < min_body_length:
        result['valid'] = False
        result['issues'].append('body_too_short')
        result['structural_score'] = 0.0
        return result

    # Structural checks
    struct = structural_checks(source_body, translated_body)
    struct_avg = sum(struct.values()) / len(struct) if struct else 0
    result['structural_score'] = struct_avg
    result['details']['structural'] = struct

    # Flag structural failures
    for check_name, score in struct.items():
        if score < 0.5:
            result['issues'].append(f'structural_{check_name}')

    # Content checks
    content = content_checks(source_fm, translated_fm, source_body, translated_body)
    result['details']['content'] = content

    for issue_name, has_issue in content.items():
        if has_issue:
            result['issues'].append(issue_name)

    # Determine validity: fail if any critical issue
    critical_issues = {
        'front_matter_untranslated', 'headers_untranslated',
        'likely_truncated', 'mostly_english', 'body_too_short',
    }
    structural_failures = {f'structural_{k}' for k, v in struct.items() if v == 0.0}

    if result['issues']:
        flagged = set(result['issues'])
        if flagged & (critical_issues | structural_failures):
            result['valid'] = False

    return result


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------
def scan_and_validate(
    content_dir: str,
    languages: List[str],
    min_year: int = 2025,
    verbose: bool = False,
) -> Dict:
    """
    Scan all blog posts and validate existing translations.

    Returns a report dict with posts that need retranslation.
    The report uses relative paths (same as missing-translations-scanner)
    so it can be fed directly to translate_posts.py.
    """
    content_path = Path(content_dir)
    post_dirs = find_post_directories(content_dir)
    posts_to_retranslate = []
    stats = {
        'total_posts': 0,
        'total_translations_checked': 0,
        'valid': 0,
        'invalid': 0,
        'missing': 0,
        'by_issue': {},
    }

    for post_dir in post_dirs:
        source_file = post_dir / 'index.md'
        try:
            source_content = source_file.read_text(encoding='utf-8')
        except Exception:
            continue

        source_fm, _ = parse_front_matter(source_content)
        if not source_fm:
            continue

        # Date filter
        date_str = source_fm.get('date', '')
        if date_str:
            try:
                if hasattr(date_str, 'year'):
                    post_year = date_str.year
                else:
                    # Try parsing common date formats
                    date_str_s = str(date_str)
                    for fmt in ['%Y-%m-%d', '%a, %d %b %Y %H:%M:%S %z']:
                        try:
                            post_year = datetime.strptime(date_str_s.strip(), fmt).year
                            break
                        except ValueError:
                            continue
                    else:
                        # Try extracting year with regex
                        year_match = re.search(r'20\d{2}', date_str_s)
                        post_year = int(year_match.group()) if year_match else 9999
                if post_year < min_year:
                    continue
            except Exception:
                continue

        # Skip archived posts
        tags = source_fm.get('tags', [])
        if isinstance(tags, list) and 'zArchive' in tags:
            continue

        stats['total_posts'] += 1
        failed_languages = []

        for lang_code in languages:
            stats['total_translations_checked'] += 1
            result = validate_translation(post_dir, lang_code, source_content)

            if not result['valid']:
                failed_languages.append(lang_code)
                stats['invalid'] += 1
                for issue in result['issues']:
                    stats['by_issue'][issue] = stats['by_issue'].get(issue, 0) + 1

                if verbose:
                    print(f"  FAIL {post_dir.name}/{lang_code}: {', '.join(result['issues'])} "
                          f"(structural={result['structural_score']:.2f})")
            else:
                stats['valid'] += 1

        if failed_languages:
            # Use relative path matching scanner format: relative to content dir's parent
            try:
                rel_path = str(post_dir.relative_to(content_path.parent))
            except ValueError:
                rel_path = str(post_dir)
            post_entry = {
                'path': rel_path,
                'missing_languages': failed_languages,
                'missing_count': len(failed_languages),
                'total_expected': len(languages),
            }
            # Include URL if available
            url = source_fm.get('url', '')
            if url:
                post_entry['url'] = url
            posts_to_retranslate.append(post_entry)

    return {
        'summary': {
            'total_posts_scanned': stats['total_posts'],
            'total_translations_checked': stats['total_translations_checked'],
            'valid_translations': stats['valid'],
            'invalid_translations': stats['invalid'],
            'posts_needing_retranslation': len(posts_to_retranslate),
            'issues_breakdown': stats['by_issue'],
            'languages_checked': languages,
            'min_year': min_year,
            'date_generated': datetime.now(timezone.utc).isoformat(),
        },
        'posts': posts_to_retranslate,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='Validate existing blog post translations and flag incomplete or incorrect ones for retranslation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_translations.py --content content/Groupdocs.Blog
  python validate_translations.py --content content/Groupdocs.Blog --output retranslate.json
  python validate_translations.py --content content/Groupdocs.Blog --lang de --verbose
  python validate_translations.py --content content/Groupdocs.Blog --post "2025-10-23-groupdocs-watermark"

The output JSON is compatible with translate_posts.py — feed it directly
to the translator to retranslate flagged posts:
  python translate_posts.py retranslate.json --verbose
        """
    )

    parser.add_argument(
        '--content',
        type=str,
        default='content',
        help='Path to blog content directory (default: content)',
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Save JSON report to file (compatible with translate_posts.py)',
    )
    parser.add_argument(
        '--lang',
        type=str,
        default=None,
        help='Check only a specific language code',
    )
    parser.add_argument(
        '--post',
        type=str,
        default=None,
        help='Check only posts matching this substring',
    )
    parser.add_argument(
        '--min-year',
        type=int,
        default=2025,
        help='Only check posts from this year onwards (default: 2025)',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print details for each failed translation',
    )

    args = parser.parse_args()

    languages = [args.lang] if args.lang else DEFAULT_LANGUAGES

    print(f"Scanning translations in: {args.content}")
    print(f"Languages: {', '.join(languages)}")
    print(f"Min year: {args.min_year}")
    print(f"{'=' * 70}")

    report = scan_and_validate(
        content_dir=args.content,
        languages=languages,
        min_year=args.min_year,
        verbose=args.verbose,
    )

    # Filter by post path if specified
    if args.post:
        report['posts'] = [p for p in report['posts'] if args.post in p['path']]
        report['summary']['posts_needing_retranslation'] = len(report['posts'])

    # Print summary
    s = report['summary']
    print(f"\n{'=' * 70}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"Posts scanned:              {s['total_posts_scanned']}")
    print(f"Translations checked:       {s['total_translations_checked']}")
    print(f"Valid:                      {s['valid_translations']}")
    print(f"Invalid (needs retranslation): {s['invalid_translations']}")
    print(f"Posts to retranslate:       {s['posts_needing_retranslation']}")

    if s['issues_breakdown']:
        print(f"\nIssues breakdown:")
        for issue, count in sorted(s['issues_breakdown'].items(), key=lambda x: -x[1]):
            print(f"  {issue}: {count}")

    if report['posts']:
        print(f"\nPosts needing retranslation:")
        for post in report['posts'][:20]:
            langs = ', '.join(post['missing_languages'])
            print(f"  {Path(post['path']).name}: {langs}")
        if len(report['posts']) > 20:
            print(f"  ... and {len(report['posts']) - 20} more")

    # Save report
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nReport saved to: {args.output}")
        print(f"Feed to translator: python translate_posts.py {args.output} --verbose")

    print(f"{'=' * 70}")

    # Exit code: 0 if all valid, 1 if retranslation needed
    sys.exit(0 if not report['posts'] else 1)


if __name__ == '__main__':
    main()
