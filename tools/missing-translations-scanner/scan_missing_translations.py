#!/usr/bin/env python3
"""
Blog Translation Scanner

Scans the content folder for blog posts and identifies missing translations.
Expected languages are read from config.yml. Uses declarative filters to exclude
archived posts and posts published before 2025.
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime, timezone


def load_config(config_path: str) -> Dict:
    """Load and parse config.yml file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse config file: {e}")
        sys.exit(1)


def get_expected_languages(config: Dict) -> List[str]:
    """Extract list of expected language codes from config."""
    languages = config.get('languages', {})
    # Exclude 'en' as it's the default (index.md without language suffix)
    lang_codes = [code for code in languages.keys() if code != 'en']
    return sorted(lang_codes)


def find_blog_post_directories(content_path: str) -> List[Path]:
    """Find all blog post directories in the content folder."""
    blog_posts = []
    content_dir = Path(content_path)
    
    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_path}")
        sys.exit(1)
    
    # Look for directories that contain index.md files
    # Blog posts are typically in content/Groupdocs.Blog/{category}/{post-name}/
    for root, dirs, files in os.walk(content_dir):
        # Check if this directory contains an index.md file (base English post)
        if 'index.md' in files:
            blog_posts.append(Path(root))
    
    return sorted(blog_posts)


def parse_front_matter(post_dir: Path) -> Optional[Dict]:
    """
    Parse front-matter from blog post index.md file.
    
    Args:
        post_dir: Path to blog post directory
    
    Returns:
        Parsed front-matter dictionary or None if parsing fails
    """
    index_file = post_dir / 'index.md'
    
    if not index_file.exists():
        return None
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract front-matter (between --- markers)
        if not content.startswith('---'):
            return None
        
        # Find the end of front-matter
        end_marker = content.find('\n---', 4)  # Skip first ---
        if end_marker == -1:
            return None
        
        front_matter = content[4:end_marker]  # Skip first ---\n
        
        # Parse YAML front-matter
        return yaml.safe_load(front_matter)
    except Exception:
        return None


class PostFilter:
    """Declarative filter for blog posts."""
    
    def __init__(self, name: str, enabled: bool = True, **kwargs):
        """
        Initialize a post filter.
        
        Args:
            name: Filter name/identifier
            enabled: Whether this filter is enabled
            **kwargs: Filter-specific configuration
        """
        self.name = name
        self.enabled = enabled
        self.config = kwargs
    
    def should_skip(self, post_dir: Path, front_matter: Optional[Dict]) -> bool:
        """
        Check if a post should be skipped based on this filter.
        
        Args:
            post_dir: Path to blog post directory
            front_matter: Parsed front-matter dictionary
        
        Returns:
            True if post should be skipped, False otherwise
        """
        if not self.enabled:
            return False
        
        if not front_matter:
            return False
        
        # Route to specific filter logic based on filter name
        if self.name == 'archived':
            return self._check_archived(front_matter)
        elif self.name == 'date_range':
            return self._check_date_range(front_matter)
        elif self.name == 'tag':
            return self._check_tag(front_matter)
        else:
            return False
    
    def _check_archived(self, front_matter: Dict) -> bool:
        """Check if post has archive tag."""
        archive_tag = self.config.get('tag', 'zArchive')
        tags = front_matter.get('tags', [])
        if isinstance(tags, list):
            return archive_tag in tags
        return False
    
    def _check_date_range(self, front_matter: Dict) -> bool:
        """Check if post date falls outside allowed range."""
        date_str = front_matter.get('date')
        if not date_str:
            return False
        
        try:
            date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            year = date_obj.year
            
            # Check minimum year (skip posts before this year)
            min_year = self.config.get('min_year')
            if min_year is not None and year < min_year:
                return True
            
            # Check maximum year (skip posts after this year)
            max_year = self.config.get('max_year')
            if max_year is not None and year > max_year:
                return True
            
            return False
        except (ValueError, AttributeError):
            return False
    
    def _check_tag(self, front_matter: Dict) -> bool:
        """Check if post has specific tag."""
        required_tag = self.config.get('tag')
        if not required_tag:
            return False
        
        tags = front_matter.get('tags', [])
        if isinstance(tags, list):
            return required_tag in tags
        return False


def create_default_filters() -> List[PostFilter]:
    """
    Create default filter configuration.
    
    Returns:
        List of PostFilter instances with default configuration
    """
    return [
        PostFilter(
            name='archived',
            enabled=True,
            tag='zArchive'
        ),
        PostFilter(
            name='date_range',
            enabled=True,
            min_year=2025  # Skip posts published before 2025
        )
    ]


def should_skip_post(post_dir: Path, filters: List[PostFilter]) -> Tuple[bool, Optional[str]]:
    """
    Check if a post should be skipped based on all filters.
    
    Args:
        post_dir: Path to blog post directory
        filters: List of PostFilter instances
    
    Returns:
        Tuple of (should_skip, filter_name) where filter_name is the name of the filter that matched
    """
    front_matter = parse_front_matter(post_dir)
    
    for filter_obj in filters:
        if filter_obj.should_skip(post_dir, front_matter):
            return True, filter_obj.name
    
    return False, None


def get_translation_files(post_dir: Path) -> Set[str]:
    """Get set of language codes for which translation files exist."""
    found_langs = set()
    
    for file in post_dir.glob('index.*.md'):
        # Extract language code from filename like index.ar.md -> ar
        parts = file.stem.split('.')
        if len(parts) == 2:
            lang_code = parts[1]
            found_langs.add(lang_code)
    
    return found_langs


def extract_front_matter_url(post_dir: Path, lang_code: str = None) -> Optional[str]:
    """
    Extract URL from front-matter of markdown file.
    
    Args:
        post_dir: Path to blog post directory
        lang_code: Language code (None for English)
    
    Returns:
        URL path from front-matter or None if not found
    """
    # Determine which markdown file to read
    if lang_code and lang_code != 'en':
        md_file = post_dir / f'index.{lang_code}.md'
    else:
        md_file = post_dir / 'index.md'
    
    if not md_file.exists():
        return None
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract front-matter (between --- markers)
        if not content.startswith('---'):
            return None
        
        # Find the end of front-matter
        end_marker = content.find('\n---', 4)  # Skip first ---
        if end_marker == -1:
            return None
        
        front_matter = content[4:end_marker]  # Skip first ---\n
        
        # Parse YAML front-matter
        front_matter_data = yaml.safe_load(front_matter)
        
        # Extract url parameter
        return front_matter_data.get('url')
    except Exception:
        return None


def extract_url_from_post(post_dir: Path, base_url: str, lang_code: str = None) -> Optional[str]:
    """
    Extract full URL from blog post front-matter.
    
    Args:
        post_dir: Path to blog post directory
        base_url: Base URL from config (e.g., 'https://blog.groupdocs.com/')
        lang_code: Language code for language-specific URL (None for English)
    
    Returns:
        Full URL for the blog post or None if not found
    """
    # Extract URL path from front-matter
    url_path = extract_front_matter_url(post_dir, lang_code)
    
    if not url_path:
        return None
    
    # Ensure base_url ends with /
    base = base_url.rstrip('/')
    
    # Combine base URL with path from front-matter
    # url_path already starts with /, so we just combine them
    return base + url_path


def scan_missing_translations(
    content_path: str,
    config_path: str,
    filters: Optional[List[PostFilter]] = None,
    verbose: bool = False
) -> Tuple[Dict[str, List[str]], Dict[str, int], List[str], int, str, Dict[str, Path], Dict[str, int], List[Dict]]:
    """
    Scan blog posts and identify missing translations.
    
    Args:
        content_path: Path to content directory
        config_path: Path to config.yml file
        filters: List of PostFilter instances (defaults to default filters if None)
        verbose: Enable verbose output
    
    Returns:
        Tuple of (missing_translations dict, statistics dict, expected_langs list, total_posts count, base_url, post_dirs, filter_counts, applied_filters)
        missing_translations: {post_path: [missing_lang_codes]}
        statistics: {lang_code: missing_count}
        expected_langs: List of expected language codes
        total_posts: Total number of blog posts scanned (excluding filtered posts)
        base_url: Base URL from config
        post_dirs: {post_path: Path} mapping for URL extraction
        filter_counts: {filter_name: count} mapping of filtered posts by filter name
        applied_filters: List of dictionaries describing applied filters
    """
    # Load configuration
    config = load_config(config_path)
    expected_langs = get_expected_languages(config)
    base_url = config.get('baseURL', 'https://blog.groupdocs.com/')
    
    # Use default filters if none provided
    if filters is None:
        filters = create_default_filters()
    
    if verbose:
        print(f"Expected languages: {', '.join(expected_langs)}")
        print(f"Total expected languages: {len(expected_langs)}")
        enabled_filters = [f.name for f in filters if f.enabled]
        if enabled_filters:
            print(f"Active filters: {', '.join(enabled_filters)}")
        print()
    
    # Find all blog post directories
    blog_posts = find_blog_post_directories(content_path)
    
    if verbose:
        print(f"Found {len(blog_posts)} blog post directories")
        print()
    
    # Apply filters and scan each blog post
    missing_translations = {}
    lang_statistics = defaultdict(int)
    post_dirs = {}  # Map post_path to Path object for URL extraction
    filter_counts = defaultdict(int)  # Track filtered posts by filter name
    
    for post_dir in blog_posts:
        rel_path = post_dir.relative_to(Path(content_path).parent)
        
        # Check if post should be skipped by any filter
        should_skip, filter_name = should_skip_post(post_dir, filters)
        if should_skip:
            filter_counts[filter_name] += 1
            if verbose:
                print(f"Skipping post (filter: {filter_name}): {rel_path}")
            continue
        
        found_langs = get_translation_files(post_dir)
        missing_langs = [lang for lang in expected_langs if lang not in found_langs]
        
        if missing_langs:
            path_str = str(rel_path)
            missing_translations[path_str] = missing_langs
            post_dirs[path_str] = post_dir
            
            # Update statistics
            for lang in missing_langs:
                lang_statistics[lang] += 1
    
    if verbose:
        for filter_name, count in filter_counts.items():
            print(f"Skipped {count} posts (filter: {filter_name})")
        if filter_counts:
            print()
    
    filtered_count = sum(filter_counts.values())
    
    # Build list of applied filters for reporting
    applied_filters = []
    for filter_obj in filters:
        if filter_obj.enabled:
            filter_info = {
                "name": filter_obj.name,
                "config": filter_obj.config.copy()
            }
            applied_filters.append(filter_info)
    
    return missing_translations, dict(lang_statistics), expected_langs, len(blog_posts) - filtered_count, base_url, post_dirs, dict(filter_counts), applied_filters


def generate_json_report(
    missing_translations: Dict[str, List[str]],
    statistics: Dict[str, int],
    expected_langs: List[str],
    total_posts: int,
    base_url: str,
    post_dirs: Dict[str, Path],
    filter_counts: Dict[str, int],
    applied_filters: List[Dict]
) -> Dict:
    """Generate JSON report structure."""
    # Convert missing_translations to list of objects for better JSON structure
    posts_with_missing = []
    for post_path in sorted(missing_translations.keys()):
        missing_langs = missing_translations[post_path]
        post_dir = post_dirs.get(post_path)
        
        if not post_dir:
            # Fallback: skip URL extraction if post_dir not found
            posts_with_missing.append({
                "path": post_path,
                "url": None,
                "urls": {},
                "missing_languages": missing_langs,
                "missing_count": len(missing_langs),
                "total_expected": len(expected_langs)
            })
            continue
        
        # Generate URLs for all languages from front-matter
        url_en = extract_url_from_post(post_dir, base_url)
        urls_by_lang = {}
        
        if url_en:
            urls_by_lang["en"] = url_en
        
        # Generate URLs for all expected languages
        for lang in expected_langs:
            url = extract_url_from_post(post_dir, base_url, lang)
            if url:
                urls_by_lang[lang] = url
        
        posts_with_missing.append({
            "path": post_path,
            "url": url_en,
            "urls": urls_by_lang,
            "missing_languages": missing_langs,
            "missing_count": len(missing_langs),
            "total_expected": len(expected_langs)
        })
    
    # Generate timestamp
    generated_at = datetime.now(timezone.utc).isoformat()
    
    report = {
        "summary": {
            "total_posts_scanned": total_posts,
            "posts_with_missing_translations": len(missing_translations),
            "posts_complete": total_posts - len(missing_translations),
            "filters_applied": applied_filters,
            "filters_counts": filter_counts,
            "expected_languages": expected_langs,
            "total_expected_languages": len(expected_langs),
            "all_complete": len(missing_translations) == 0,
            "base_url": base_url,
            "date_generated": generated_at
        },
        "posts": posts_with_missing
    }
    
    return report


def print_text_report(
    missing_translations: Dict[str, List[str]],
    statistics: Dict[str, int],
    expected_langs: List[str],
    total_posts: int,
    filter_counts: Dict[str, int],
    applied_filters: List[Dict]
):
    """Print human-readable text report to console."""
    output_lines = []
    
    # Header
    output_lines.append("=" * 80)
    output_lines.append("BLOG POST TRANSLATION SCANNER REPORT")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Summary statistics
    posts_with_missing = len(missing_translations)
    total_expected = len(expected_langs)
    
    # Generate timestamp for display
    generated_at = datetime.now(timezone.utc)
    generated_at_str = generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    output_lines.append("SUMMARY")
    output_lines.append("-" * 80)
    output_lines.append(f"Date generated: {generated_at_str}")
    output_lines.append(f"Total blog posts scanned: {total_posts}")
    
    # Show applied filters
    if applied_filters:
        output_lines.append("Applied filters:")
        for filter_info in applied_filters:
            filter_name = filter_info.get('name', 'unknown')
            filter_config = filter_info.get('config', {})
            config_str = ', '.join([f"{k}={v}" for k, v in filter_config.items()])
            if config_str:
                output_lines.append(f"  - {filter_name} ({config_str})")
            else:
                output_lines.append(f"  - {filter_name}")
        output_lines.append("")
    
    # Show filter counts
    if filter_counts:
        output_lines.append("Posts filtered by filter:")
        for filter_name, count in sorted(filter_counts.items()):
            output_lines.append(f"  {filter_name}: {count}")
        output_lines.append("")
    
    output_lines.append(f"Posts with missing translations: {posts_with_missing}")
    output_lines.append(f"Posts with complete translations: {total_posts - posts_with_missing}")
    output_lines.append(f"Expected languages: {total_expected}")
    output_lines.append("")
    
    # Detailed report
    if missing_translations:
        output_lines.append("DETAILED REPORT")
        output_lines.append("-" * 80)
        
        sorted_posts = sorted(missing_translations.items())
        for post_path, missing_langs in sorted_posts:
            output_lines.append(f"\nPost: {post_path}")
            output_lines.append(f"  Missing translations: {', '.join(missing_langs)}")
            output_lines.append(f"  Missing count: {len(missing_langs)}/{len(expected_langs)}")
    else:
        output_lines.append("✓ All blog posts have complete translations!")
        output_lines.append("")
    
    output_lines.append("")
    output_lines.append("=" * 80)
    
    # Output to console
    report_text = "\n".join(output_lines)
    print(report_text)


def save_json_report(
    report: Dict,
    output_file: str,
    indent: int = 2
):
    """Save JSON report to file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=indent, ensure_ascii=False)
        print(f"\nJSON report saved to: {output_file}", file=sys.stderr)
    except Exception as e:
        print(f"\nError saving JSON report to file: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scan blog posts for missing translations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_missing_translations.py
  python scan_missing_translations.py --verbose
  python scan_missing_translations.py --output translations_scan_report.json
  python scan_missing_translations.py --content ../content --config ../config.yml
        """
    )
    
    parser.add_argument(
        '--content',
        type=str,
        default='content',
        help='Path to content directory (default: content)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yml',
        help='Path to config.yml file (default: config.yml)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path for the JSON report (optional)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    
    content_path = repo_root / args.content
    config_path = repo_root / args.config
    
    # Scan for missing translations
    missing_translations, statistics, expected_langs, total_posts, base_url, post_dirs, filter_counts, applied_filters = scan_missing_translations(
        str(content_path),
        str(config_path),
        filters=None,  # Use default filters
        verbose=args.verbose
    )
    
    # Print text report to console
    print_text_report(
        missing_translations,
        statistics,
        expected_langs,
        total_posts,
        filter_counts,
        applied_filters
    )
    
    # Save JSON report to file if requested
    if args.output:
        report = generate_json_report(
            missing_translations,
            statistics,
            expected_langs,
            total_posts,
            base_url,
            post_dirs,
            filter_counts,
            applied_filters
        )
        save_json_report(
            report,
            args.output,
            indent=2
        )
    
    # Exit with error code if missing translations found
    if missing_translations:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

