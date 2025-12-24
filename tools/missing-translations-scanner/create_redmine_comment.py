#!/usr/bin/env python3
"""
Create a formatted comment for Redmine about missing translations scan.

This script reads the translations_scan_report.json file and creates a formatted comment
that can be used with redmine-activity-reporter.
"""

import json
import sys
import argparse
import os


def create_redmine_comment(report: dict, user_mention: str = None, action_url: str = None) -> str:
    """
    Create formatted comment for Redmine.
    
    Args:
        report: Translation scan report dictionary
        user_mention: Optional user mention to include at the beginning (e.g., "@username")
        action_url: Optional GitHub Actions run URL to include at the end
    
    Returns:
        Formatted comment text
    """
    summary = report.get('summary', {})
    posts = report.get('posts', [])
    
    posts_with_missing = summary.get('posts_with_missing_translations', 0)
    total_posts = summary.get('total_posts_scanned', 0)
    
    comment = ""
    
    # Add user mention if provided
    if user_mention:
        comment += f"{user_mention}\n\n"
    
    comment += "Blog Post Translation Scan Results\n\n"
    comment += f"Scanned {total_posts} blog post(s). Found {posts_with_missing} untranslated blog post(s).\n\n"
    
    if posts_with_missing > 0:
        comment += "Untranslated blog posts:\n\n"
        
        # Sort by missing_count descending, then by post path
        sorted_posts = sorted(posts, key=lambda x: (x.get('missing_count', 0), x.get('path', '')), reverse=True)
        
        for post in sorted_posts:
            post_path = post.get('path', '')
            post_name = post_path.split('/')[-1] if '/' in post_path else post_path
            url = post.get('url', '')
            missing_count = post.get('missing_count', 0)
            total_expected = post.get('total_expected', 0)
            missing_langs = post.get('missing_languages', [])
            
            # Create formatted line with link if URL is available
            if url:
                comment += f"* {post_name}: {url}\n"
            else:
                comment += f"* {post_name}\n"
            
            comment += f"  Missing translations: {missing_count}/{total_expected} ({', '.join(missing_langs)})\n"
    else:
        comment += "✓ All blog posts have complete translations!\n"
    
    # Add action URL if provided
    if action_url:
        comment += f"\nGitHub Actions run: {action_url}"
    
    return comment


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create Redmine comment for missing translations scan',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--report-json',
        type=str,
        required=True,
        help='Path to JSON file with translation scan report'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='-',
        help='Output file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Read scan report
    try:
        with open(args.report_json, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except FileNotFoundError:
        print(f"Error: Scan report file not found: {args.report_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get user mention from environment variable if available
    user_mention = os.environ.get('REDMINE_REPORT_TO_USER')
    
    # Construct GitHub Actions run URL from environment variables
    action_url = None
    github_server = os.environ.get('GITHUB_SERVER_URL')
    github_repo = os.environ.get('GITHUB_REPOSITORY')
    github_run_id = os.environ.get('GITHUB_RUN_ID')
    
    if github_server and github_repo and github_run_id:
        action_url = f"{github_server}/{github_repo}/actions/runs/{github_run_id}"
    
    # Create comment
    comment = create_redmine_comment(report, user_mention=user_mention, action_url=action_url)
    
    # Output comment
    if args.output == '-':
        print(comment)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(comment)


if __name__ == '__main__':
    main()
