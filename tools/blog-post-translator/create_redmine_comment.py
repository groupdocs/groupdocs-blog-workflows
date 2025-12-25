#!/usr/bin/env python3
"""
Create a formatted comment for Redmine about translated blog posts.

This script reads the translated_posts.json file and creates a formatted comment
that can be used with redmine-activity-reporter.
"""

import json
import sys
import argparse
import os


def create_redmine_comment(posts_dict: dict, user_mention: str = None, action_url: str = None) -> str:
    """
    Create formatted comment for Redmine.
    
    Args:
        posts_dict: Dictionary mapping post paths to dicts with 'languages' and 'url'
        user_mention: Optional user mention to include at the beginning (e.g., "@username")
        action_url: Optional Job URL to include at the end
    
    Returns:
        Formatted comment text
    """
    comment = ""
    
    # Add user mention if provided
    if user_mention:
        comment += f"{user_mention}\n\n"
    
    comment += "The following blog posts have been automatically translated:\n\n"
    
    for post_path, post_info in posts_dict.items():
        post_name = post_path.split('/')[-1] if '/' in post_path else post_path
        
        # Handle both old format (list of languages) and new format (dict with languages and url)
        if isinstance(post_info, list):
            # Old format: just a list of language codes
            langs = post_info
            url = ''
        else:
            # New format: dict with 'languages' and 'url'
            langs = post_info.get('languages', [])
            url = post_info.get('url', '')
        
        # Create formatted line with link if URL is available
        # Redmine supports both Textile and Markdown, using simple format that works in both
        if url:
            comment += f"* {post_name}: {url}\n"
            comment += f"  Languages: {', '.join(langs)}\n"
        else:
            comment += f"* {post_name}\n"
            comment += f"  Languages: {', '.join(langs)}\n"
    
    # Add action URL if provided
    if action_url:
        comment += f"\nJob: {action_url}"
    
    return comment


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create Redmine comment for translated blog posts',
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
    
    # Get user mention from environment variable if available
    user_mention = os.environ.get('REDMINE_REPORT_TO_USER')
    
    # Construct Job URL from environment variables
    action_url = None
    github_server = os.environ.get('GITHUB_SERVER_URL')
    github_repo = os.environ.get('GITHUB_REPOSITORY')
    github_run_id = os.environ.get('GITHUB_RUN_ID')
    
    if github_server and github_repo and github_run_id:
        action_url = f"{github_server}/{github_repo}/actions/runs/{github_run_id}"
    
    # Create comment
    comment = create_redmine_comment(posts_dict, user_mention=user_mention, action_url=action_url)
    
    # Output comment
    if args.output == '-':
        print(comment)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(comment)


if __name__ == '__main__':
    main()
