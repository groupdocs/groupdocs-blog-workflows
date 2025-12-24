#!/usr/bin/env python3
"""
Log historical translation work from GitHub issues to Redmine.

This script reads all GitHub issues from the blog repository where the title
contains "Automated Translation", extracts the translation information from
the issue body, and logs the work to Redmine using the issue creation date.
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.error
import re
from datetime import datetime
from typing import List, Dict, Optional


def fetch_github_issues(repo: str, github_token: str, title_filter: str = "Automated Translation") -> List[Dict]:
    """
    Fetch all issues from a GitHub repository that match the title filter.
    
    Args:
        repo: GitHub repository in format "owner/repo"
        github_token: GitHub personal access token
        title_filter: String that must be contained in the issue title
    
    Returns:
        List of issue dictionaries
    """
    issues = []
    page = 1
    per_page = 100
    
    while True:
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            "state": "all",  # Get both open and closed issues
            "page": page,
            "per_page": per_page
        }
        
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Build URL with query parameters
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{query_string}"
        
        req = urllib.request.Request(full_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                page_issues = json.loads(response.read().decode('utf-8'))
                
                # Filter issues by title and exclude pull requests
                filtered_issues = [
                    issue for issue in page_issues
                    if 'pull_request' not in issue  # Exclude pull requests
                    and title_filter.lower() in issue.get('title', '').lower()
                ]
                issues.extend(filtered_issues)
                
                # If we got fewer than per_page, we're done
                if len(page_issues) < per_page:
                    break
                
                page += 1
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Error: Failed to fetch issues: {e.code} {e.reason}", file=sys.stderr)
            print(error_body, file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Unexpected error fetching issues: {e}", file=sys.stderr)
            sys.exit(1)
    
    return issues


def clean_issue_body(body: str) -> str:
    """
    Remove header and footer from issue body.
    
    Removes:
    - Header: "## Automated Blog Post Translation\n\n"
    - Footer: "\n---\n*This issue was automatically created by the translation workflow.*"
    
    Args:
        body: Original issue body
    
    Returns:
        Cleaned body text
    """
    cleaned = body.strip()
    
    # Remove header
    header = "## Automated Blog Post Translation\n\n"
    if cleaned.startswith(header):
        cleaned = cleaned[len(header):]
    
    # Remove footer (handle with or without trailing newline/whitespace)
    footer_patterns = [
        "\n---\n*This issue was automatically created by the translation workflow.*",
        "\n---\n*This issue was automatically created by the translation workflow.*\n",
        "---\n*This issue was automatically created by the translation workflow.*",
    ]
    
    for footer in footer_patterns:
        if cleaned.endswith(footer):
            cleaned = cleaned[:-len(footer)]
            break
        # Also try with stripped version
        if cleaned.rstrip().endswith(footer.rstrip()):
            cleaned = cleaned[:cleaned.rstrip().rfind(footer.rstrip())]
            break
    
    return cleaned.strip()


def parse_issue_date(created_at: str) -> str:
    """
    Parse GitHub issue creation date and return in YYYY-MM-DD format.
    
    Args:
        created_at: ISO 8601 date string from GitHub API
    
    Returns:
        Date string in YYYY-MM-DD format
    """
    # GitHub API returns dates in ISO 8601 format: "2024-01-15T10:30:00Z"
    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d')


def extract_urls_from_body(body: str) -> List[str]:
    """
    Extract URLs from issue body.
    
    Looks for markdown links [text](url) and plain URLs.
    
    Args:
        body: Issue body text
    
    Returns:
        List of URLs found
    """
    urls = []
    
    # Extract markdown links: [text](url)
    markdown_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(markdown_link_pattern, body):
        url = match.group(2)
        if url.startswith('http'):
            urls.append(url)
    
    # Also extract plain URLs (http:// or https://)
    plain_url_pattern = r'https?://[^\s\)]+'
    for match in re.finditer(plain_url_pattern, body):
        url = match.group(0).rstrip('.,;:!?)')
        if url not in urls:
            urls.append(url)
    
    return urls


def create_simplified_time_comment(urls: List[str]) -> str:
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


def log_to_redmine(
    redmine_endpoint: str,
    redmine_api_key: str,
    issue_id: str,
    hours: float,
    activity_id: int,
    issue_comment: str,
    time_comment: str,
    spent_on: str
) -> bool:
    """
    Log time to Redmine and add comment to issue using the redmine-activity-reporter module.
    
    Args:
        redmine_endpoint: Redmine base URL
        redmine_api_key: Redmine API key
        issue_id: Redmine issue ID
        hours: Number of hours to log
        activity_id: Activity type ID
        issue_comment: Full comment to add to the issue
        time_comment: Simplified comment for the time entry
        spent_on: Date in YYYY-MM-DD format
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import the RedmineActivityReporter class
        # Get the absolute path to the redmine-activity-reporter directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tools_dir = os.path.dirname(script_dir)
        redmine_dir = os.path.join(tools_dir, 'redmine-activity-reporter')
        sys.path.insert(0, redmine_dir)
        from redmine_activity_reporter import RedmineActivityReporter
        
        reporter = RedmineActivityReporter(redmine_endpoint, redmine_api_key)
        
        # Add comment to the issue
        reporter.add_comment(
            issue_identifier=issue_id,
            comment=issue_comment
        )
        
        # Log time with simplified comment
        reporter.log_time(
            issue_identifier=issue_id,
            hours=hours,
            activity_id=activity_id,
            comments=time_comment,
            spent_on=spent_on
        )
        
        return True
    except Exception as e:
        print(f"Error logging to Redmine: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Log historical translation work from GitHub issues to Redmine',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        default='groupdocs/groupdocs-blog',
        help='GitHub repository in format "owner/repo" (default: groupdocs/groupdocs-blog)'
    )
    
    parser.add_argument(
        '--github-token',
        type=str,
        default=None,
        help='GitHub personal access token (or use GITHUB_TOKEN env var)'
    )
    
    parser.add_argument(
        '--redmine-endpoint',
        type=str,
        default=None,
        help='Redmine endpoint URL (or use REDMINE_ENDPOINT env var)'
    )
    
    parser.add_argument(
        '--redmine-api-key',
        type=str,
        default=None,
        help='Redmine API key (or use REDMINE_API_KEY env var)'
    )
    
    parser.add_argument(
        '--redmine-issue-id',
        type=str,
        required=True,
        help='Redmine issue ID to log time to'
    )
    
    parser.add_argument(
        '--activity-id',
        type=int,
        default=None,
        help='Activity type ID (or use REDMINE_ACTIVITY_ID_LOCALIZATION env var, default: 65)'
    )
    
    parser.add_argument(
        '--hours',
        type=float,
        default=1.0,
        help='Hours to log per issue (default: 1.0)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print what would be logged without actually logging to Redmine'
    )
    
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = args.github_token or os.environ.get('GITHUB_TOKEN') or os.environ.get('REPO_PAT')
    if not github_token:
        print("Error: GitHub token not provided. Use --github-token or set GITHUB_TOKEN/REPO_PAT env var.", file=sys.stderr)
        sys.exit(1)
    
    # Get Redmine credentials
    redmine_endpoint = args.redmine_endpoint or os.environ.get('REDMINE_ENDPOINT')
    redmine_api_key = args.redmine_api_key or os.environ.get('REDMINE_API_KEY')
    
    if not args.dry_run:
        if not redmine_endpoint:
            print("Error: Redmine endpoint not provided. Use --redmine-endpoint or set REDMINE_ENDPOINT env var.", file=sys.stderr)
            sys.exit(1)
        if not redmine_api_key:
            print("Error: Redmine API key not provided. Use --redmine-api-key or set REDMINE_API_KEY env var.", file=sys.stderr)
            sys.exit(1)
    
    # Get activity ID
    activity_id = args.activity_id
    if activity_id is None:
        activity_id_str = os.environ.get('REDMINE_ACTIVITY_ID_LOCALIZATION', '65')
        try:
            activity_id = int(activity_id_str)
        except ValueError:
            print(f"Warning: Invalid activity ID '{activity_id_str}', using default 65", file=sys.stderr)
            activity_id = 65
    
    # Fetch issues
    print(f"Fetching issues from {args.repo}...", file=sys.stderr)
    issues = fetch_github_issues(args.repo, github_token, "Automated Translation")
    print(f"Found {len(issues)} issues matching 'Automated Translation'", file=sys.stderr)
    
    if not issues:
        print("No issues found to process.", file=sys.stderr)
        return
    
    # Process each issue
    success_count = 0
    error_count = 0
    
    for issue in issues:
        issue_number = issue.get('number')
        issue_title = issue.get('title', '')
        issue_body = issue.get('body', '')
        created_at = issue.get('created_at', '')
        
        if not issue_body:
            print(f"Skipping issue #{issue_number}: empty body", file=sys.stderr)
            continue
        
        # Clean the issue body
        cleaned_body = clean_issue_body(issue_body)
        
        if not cleaned_body:
            print(f"Skipping issue #{issue_number}: no content after cleaning", file=sys.stderr)
            continue
        
        # Extract URLs from the cleaned body
        urls = extract_urls_from_body(cleaned_body)
        
        # Create simplified time comment with just URLs
        time_comment = create_simplified_time_comment(urls)
        
        # Prepend user mention if provided for the issue comment
        user_mention = os.environ.get('REDMINE_REPORT_TO_USER')
        if user_mention:
            issue_comment = f"{user_mention}\n\n{cleaned_body}"
        else:
            issue_comment = cleaned_body
        
        # Parse the creation date
        try:
            spent_on = parse_issue_date(created_at)
        except Exception as e:
            print(f"Error parsing date for issue #{issue_number}: {e}", file=sys.stderr)
            error_count += 1
            continue
        
        # Log to Redmine
        if args.dry_run:
            print(f"\n[DRY RUN] Would log to Redmine:", file=sys.stderr)
            print(f"  Issue: {args.redmine_issue_id}", file=sys.stderr)
            print(f"  Hours: {args.hours}", file=sys.stderr)
            print(f"  Activity ID: {activity_id}", file=sys.stderr)
            print(f"  Date: {spent_on}", file=sys.stderr)
            print(f"  Issue Comment: {issue_comment[:100]}...", file=sys.stderr)
            print(f"  Time Comment: {time_comment}", file=sys.stderr)
            success_count += 1
        else:
            print(f"Logging issue #{issue_number} (created {spent_on})...", file=sys.stderr)
            if log_to_redmine(
                redmine_endpoint,
                redmine_api_key,
                args.redmine_issue_id,
                args.hours,
                activity_id,
                issue_comment,
                time_comment,
                spent_on
            ):
                print(f"✓ Successfully logged issue #{issue_number}", file=sys.stderr)
                success_count += 1
            else:
                print(f"✗ Failed to log issue #{issue_number}", file=sys.stderr)
                error_count += 1
    
    # Summary
    print(f"\nSummary:", file=sys.stderr)
    print(f"  Successfully processed: {success_count}", file=sys.stderr)
    print(f"  Errors: {error_count}", file=sys.stderr)
    
    if error_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
