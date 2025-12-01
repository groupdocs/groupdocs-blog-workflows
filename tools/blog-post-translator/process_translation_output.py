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


def extract_translated_posts(output_file: str) -> dict:
    """
    Extract translated posts information from translation output.
    
    Args:
        output_file: Path to translation output file
    
    Returns:
        Dictionary mapping post paths to lists of language codes
    """
    # Read translation output
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            output = f.read()
    except FileNotFoundError:
        print(f"Warning: Translation output file not found: {output_file}", file=sys.stderr)
        return {}
    
    # Extract translated posts from output
    translated_posts = []
    current_post = None
    
    for line in output.split('\n'):
        if 'Processing:' in line:
            # Extract post path
            match = re.search(r'Processing:\s*(.+)', line)
            if match:
                current_post = match.group(1).strip()
        elif 'Translating to' in line and '✓' in line:
            # Extract language
            match = re.search(r'Translating to\s+(\w+(-\w+)?)', line)
            if match and current_post:
                lang = match.group(1)
                translated_posts.append({
                    'path': current_post,
                    'language': lang
                })
    
    # Group by post
    posts_dict = {}
    for item in translated_posts:
        post_path = item['path']
        if post_path not in posts_dict:
            posts_dict[post_path] = []
        posts_dict[post_path].append(item['language'])
    
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
    
    args = parser.parse_args()
    
    # Extract translated posts
    posts_dict = extract_translated_posts(args.input)
    
    # Save to JSON file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(posts_dict, f, indent=2)
    
    # Output summary
    if posts_dict:
        print(f"Translated {len(posts_dict)} post(s)", file=sys.stderr)
        for post_path, langs in posts_dict.items():
            print(f"  - {post_path}: {', '.join(langs)}", file=sys.stderr)
        # Exit with success code if translations were found
        sys.exit(0)
    else:
        print("No translations completed", file=sys.stderr)
        # Exit with code 1 if no translations were found
        sys.exit(1)


if __name__ == '__main__':
    main()
