#!/usr/bin/env python3
"""
Create a GitHub issue for translated blog posts.

This script reads the translated_posts.json file and creates a GitHub issue
in the blog repository listing all translated posts and their languages.
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.error


def create_issue_body(posts_dict: dict) -> str:
    """
    Create markdown body for GitHub issue.
    
    Args:
        posts_dict: Dictionary mapping post paths to dicts with 'languages' and 'url'
    
    Returns:
        Markdown formatted issue body
    """
    body = "## Automated Blog Post Translation\n\n"
    body += "The following blog posts have been automatically translated:\n\n"
    
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
        
        # Create clickable link if URL is available
        if url:
            body += f"- **[{post_name}]({url})** → Languages: {', '.join(langs)}\n"
        else:
            body += f"- **{post_name}** → Languages: {', '.join(langs)}\n"
    
    body += "\n---\n"
    body += "*This issue was automatically created by the translation workflow.*"
    
    return body


def create_github_issue(
    posts_json_path: str,
    repo: str,
    github_token: str,
    title: str = "Automated Translation: Blog Posts Translated"
) -> str:
    """
    Create a GitHub issue with translated posts information.
    
    Args:
        posts_json_path: Path to JSON file with translated posts
        repo: GitHub repository in format "owner/repo"
        github_token: GitHub personal access token
        title: Issue title
    
    Returns:
        URL of created issue
    
    Raises:
        SystemExit: If issue creation fails
    """
    # Read translated posts
    try:
        with open(posts_json_path, 'r', encoding='utf-8') as f:
            posts_dict = json.load(f)
    except FileNotFoundError:
        print(f"Error: Translated posts file not found: {posts_json_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not posts_dict:
        print("Error: No translated posts found in file", file=sys.stderr)
        sys.exit(1)
    
    # Create issue body
    body = create_issue_body(posts_dict)
    
    # Create issue payload
    issue_data = {
        "title": title,
        "body": body
    }
    
    # Create request
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(issue_data).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            issue_url = response_data.get('html_url', '')
            if issue_url:
                print(f"Issue created: {issue_url}", file=sys.stderr)
                return issue_url
            else:
                print("Error: Failed to create issue - no URL in response", file=sys.stderr)
                print(json.dumps(response_data, indent=2), file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Error: Failed to create issue: {e.code} {e.reason}", file=sys.stderr)
        print(error_body, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error creating issue: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create GitHub issue for translated blog posts',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--posts-json',
        type=str,
        required=True,
        help='Path to JSON file with translated posts'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='GitHub repository in format "owner/repo"'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='GitHub personal access token (or use GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default='Automated Translation: Blog Posts Translated',
        help='Issue title'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token from argument or environment variable
    github_token = args.token or os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GitHub token not provided. Use --token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)
    
    # Create issue
    issue_url = create_github_issue(
        args.posts_json,
        args.repo,
        github_token,
        args.title
    )
    
    # Print issue URL to stdout for workflow to capture
    print(issue_url)


if __name__ == '__main__':
    main()
