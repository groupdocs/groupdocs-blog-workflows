#!/usr/bin/env python3
"""
Process translation output and extract translated posts information.

This script reads the output from translate_posts.py and creates a JSON file
with information about which posts were translated and to which languages.
"""

import json
import re
import sys
import argparse
from pathlib import Path


def load_scan_report(scan_report_path: str) -> dict:
    """
    Load the translation scan report to get URL information.
    
    Args:
        scan_report_path: Path to translations_scan_report.json
    
    Returns:
        Dictionary mapping post paths to post data (including URLs)
    """
    try:
        with open(scan_report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except FileNotFoundError:
        print(f"Warning: Scan report not found: {scan_report_path}", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse scan report: {e}", file=sys.stderr)
        return {}
    
    # Create a mapping of post paths to post data
    posts_map = {}
    for post in report.get('posts', []):
        post_path = post.get('path', '')
        if post_path:
            posts_map[post_path] = post
    
    return posts_map


def extract_translated_posts(output_file: str, scan_report_path: str = None) -> dict:
    """
    Extract translated posts information from translation output.
    
    Args:
        output_file: Path to translation output file
        scan_report_path: Optional path to translations_scan_report.json for URL info
    
    Returns:
        Dictionary mapping post paths to dicts with languages and URL
    """
    # Read translation output
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            output = f.read()
    except FileNotFoundError:
        print(f"Warning: Translation output file not found: {output_file}", file=sys.stderr)
        return {}
    
    # Check if there's a summary indicating translations were completed
    summary_match = re.search(r'Total translations completed:\s*(\d+)', output)
    if summary_match:
        total_completed = int(summary_match.group(1))
        if total_completed == 0:
            print(f"Translation summary shows 0 translations completed", file=sys.stderr)
            return {}
    
    # Extract translated posts from output
    translated_posts = []
    current_post = None
    lines = output.split('\n')
    
    for i, line in enumerate(lines):
        if 'Processing:' in line:
            # Extract post path - handle format like "[1/3] Processing: path"
            match = re.search(r'Processing:\s*(.+)', line)
            if match:
                current_post = match.group(1).strip()
        elif 'Translating to' in line and current_post:
            # Extract language
            lang_match = re.search(r'Translating to\s+(\w+(?:-\w+)?)', line)
            if lang_match:
                lang = lang_match.group(1)
                # Check if success marker (✓) is on this line or within next 2 lines
                # (handles case where print statements might be split across lines)
                check_lines = lines[i:min(i+3, len(lines))]
                combined_text = ' '.join(check_lines)
                if '✓' in combined_text:
                    # Only add if not already added
                    if not any(p['path'] == current_post and p['language'] == lang 
                              for p in translated_posts):
                        translated_posts.append({
                            'path': current_post,
                            'language': lang
                        })
    
    # Load scan report for URL information
    scan_report = {}
    if scan_report_path:
        scan_report = load_scan_report(scan_report_path)
    
    # Group by post and include URL information
    posts_dict = {}
    for item in translated_posts:
        post_path = item['path']
        if post_path not in posts_dict:
            # Get URL from scan report if available
            post_data = scan_report.get(post_path, {})
            url = post_data.get('url', '')
            
            posts_dict[post_path] = {
                'languages': [],
                'url': url
            }
        posts_dict[post_path]['languages'].append(item['language'])
    
    return posts_dict


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process translation output and extract translated posts information',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to translation output file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to output JSON file'
    )
    
    parser.add_argument(
        '--scan-report',
        type=str,
        default=None,
        help='Path to translations_scan_report.json for URL information'
    )
    
    args = parser.parse_args()
    
    # Extract translated posts
    posts_dict = extract_translated_posts(args.input, args.scan_report)
    
    # Save to JSON file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(posts_dict, f, indent=2)
    
    # Output summary
    if posts_dict:
        print(f"Translated {len(posts_dict)} post(s)", file=sys.stderr)
        for post_path, post_info in posts_dict.items():
            langs = post_info.get('languages', [])
            url = post_info.get('url', '')
            url_str = f" ({url})" if url else ""
            print(f"  - {post_path}: {', '.join(langs)}{url_str}", file=sys.stderr)
        # Exit with success code if translations were found
        sys.exit(0)
    else:
        print("No translations completed", file=sys.stderr)
        # Exit with code 1 if no translations were found
        sys.exit(1)


if __name__ == '__main__':
    main()
