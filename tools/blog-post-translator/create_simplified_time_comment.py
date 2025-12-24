#!/usr/bin/env python3
"""
Create a simplified time entry comment with just URLs from translated posts.

This script reads the translated_posts.json file and creates a simplified comment
containing only the blog post URLs for time logging.
"""

import json
import sys
import argparse


def extract_urls_from_posts(posts_dict: dict) -> list:
    """
    Extract URLs from translated posts dictionary.
    
    Args:
        posts_dict: Dictionary mapping post paths to dicts with 'languages' and 'url'
    
    Returns:
        List of URLs found
    """
    urls = []
    
    for post_path, post_info in posts_dict.items():
        # Handle both old format (list of languages) and new format (dict with languages and url)
        if isinstance(post_info, list):
            # Old format: just a list of language codes, no URL
            continue
        else:
            # New format: dict with 'languages' and 'url'
            url = post_info.get('url', '')
            if url and url.startswith('http'):
                urls.append(url)
    
    return urls


def create_simplified_time_comment(urls: list) -> str:
    """
    Create simplified time entry comment with just URLs.
    
    Args:
        urls: List of blog post URLs
    
    Returns:
        Simplified comment text
    """
    if not urls:
        return "Translated blog posts"
    
    url_list = ', '.join(urls)
    return f"Translated blog posts: {url_list}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create simplified time comment for Redmine with just URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--posts-json',
        type=str,
        required=True,
        help='Path to JSON file with translated posts'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='-',
        help='Output file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Read translated posts
    try:
        with open(args.posts_json, 'r', encoding='utf-8') as f:
            posts_dict = json.load(f)
    except FileNotFoundError:
        print(f"Error: Translated posts file not found: {args.posts_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not posts_dict:
        print("Error: No translated posts found in file", file=sys.stderr)
        sys.exit(1)
    
    # Extract URLs and create simplified comment
    urls = extract_urls_from_posts(posts_dict)
    comment = create_simplified_time_comment(urls)
    
    # Output comment
    if args.output == '-':
        print(comment)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(comment)


if __name__ == '__main__':
    main()
