#!/usr/bin/env python3
"""
Log time and add comment to Redmine issue.

This script adds a full comment to a Redmine issue and logs time with a simplified comment.
"""

import os
import sys

# Add redmine-activity-reporter to path
script_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(script_dir)
redmine_dir = os.path.join(tools_dir, 'redmine-activity-reporter')
sys.path.insert(0, redmine_dir)

from redmine_activity_reporter import RedmineActivityReporter


def main():
    """Main entry point."""
    # Get required environment variables
    redmine_endpoint = os.environ.get('REDMINE_ENDPOINT')
    redmine_api_key = os.environ.get('REDMINE_API_KEY')
    redmine_issue_id = os.environ.get('REDMINE_ISSUE_ID')
    redmine_activity_id = os.environ.get('REDMINE_ACTIVITY_ID')
    
    # Default file names
    issue_comment_file = 'redmine_comment.txt'
    time_comment_file = 'redmine_time_comment.txt'
    
    if not redmine_endpoint:
        print("Error: REDMINE_ENDPOINT environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    if not redmine_api_key:
        print("Error: REDMINE_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    if not redmine_issue_id:
        print("Error: REDMINE_ISSUE_ID environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    if not redmine_activity_id:
        print("Error: REDMINE_ACTIVITY_ID environment variable is required", file=sys.stderr)
        sys.exit(1)
    
    # Get optional environment variables
    hours = float(os.environ.get('REDMINE_HOURS', '1.0'))
    
    try:
        with open(issue_comment_file, 'r', encoding='utf-8') as f:
            issue_comment = f.read()
    except FileNotFoundError:
        print(f"Error: Issue comment file not found: {issue_comment_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(time_comment_file, 'r', encoding='utf-8') as f:
            time_comment = f.read()
    except FileNotFoundError:
        print(f"Error: Time comment file not found: {time_comment_file}", file=sys.stderr)
        sys.exit(1)
    
    # Create reporter
    reporter = RedmineActivityReporter(redmine_endpoint, redmine_api_key)
    
    try:
        # Add comment to the issue
        reporter.add_comment(
            issue_identifier=redmine_issue_id,
            comment=issue_comment
        )
        print(f"✓ Successfully added comment to issue {redmine_issue_id}", file=sys.stderr)
        
        # Log time with simplified comment
        reporter.log_time(
            issue_identifier=redmine_issue_id,
            hours=hours,
            activity_id=int(redmine_activity_id),
            comments=time_comment
        )
        print(f"✓ Successfully logged {hours} hours to issue {redmine_issue_id}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
