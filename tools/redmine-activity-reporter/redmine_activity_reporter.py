#!/usr/bin/env python3
"""
Redmine Activity Reporter
Logs time and adds comments to Redmine issues using the REST API.
Compatible with Redmine 3.4.6
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional
import requests


class RedmineActivityReporter:
    """Class to handle Redmine activity reporting (time logging and comments)."""
    
    def __init__(self, endpoint: str, api_key: str):
        """
        Initialize the Redmine reporter.
        
        Args:
            endpoint: Redmine base URL (e.g., 'https://redmine.example.com')
            api_key: Redmine API key for authentication
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Redmine-API-Key': api_key
        })
    
    def _resolve_issue_id(self, issue_identifier: str) -> int:
        """
        Resolve issue key (e.g., ISSUEKEY-1) to numeric ID.
        If already a numeric ID, returns it as int.
        
        Args:
            issue_identifier: Issue ID (numeric) or issue key (e.g., PROJECT-123)
        
        Returns:
            int: Numeric issue ID
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
            ValueError: If issue identifier is invalid
        """
        # Check if it's already a numeric ID
        try:
            return int(issue_identifier)
        except ValueError:
            # It's an issue key, need to resolve it
            pass
        
        # Fetch issue by key to get the numeric ID
        url = f"{self.endpoint}/issues/{issue_identifier}.json"
        response = self.session.get(url)
        response.raise_for_status()
        issue_data = response.json()
        return issue_data['issue']['id']
    
    def log_time(self, issue_identifier: str, hours: float, activity_id: int, 
                 comments: Optional[str] = None, spent_on: Optional[str] = None) -> dict:
        """
        Log time to a Redmine issue.
        
        Args:
            issue_identifier: The issue ID (numeric) or issue key (e.g., ISSUEKEY-1)
            hours: Number of hours to log
            activity_id: Activity type ID (e.g., 8 for Development, 9 for Design, etc.)
            comments: Optional comments for the time entry
            spent_on: Date in YYYY-MM-DD format (defaults to today)
        
        Returns:
            dict: Response from Redmine API
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        # Resolve issue key to numeric ID if needed
        issue_id = self._resolve_issue_id(issue_identifier)
        
        if spent_on is None:
            spent_on = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.endpoint}/time_entries.json"
        
        data = {
            "time_entry": {
                "issue_id": issue_id,
                "hours": hours,
                "activity_id": activity_id,
                "spent_on": spent_on
            }
        }
        
        if comments:
            data["time_entry"]["comments"] = comments
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def add_comment(self, issue_identifier: str, comment: str, 
                   notes_private: bool = False) -> dict:
        """
        Add a comment to a Redmine issue.
        
        Args:
            issue_identifier: The issue ID (numeric) or issue key (e.g., ISSUEKEY-1)
            comment: The comment text to add
            notes_private: If True, adds a private note (requires permissions)
        
        Returns:
            dict: Response from Redmine API
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        # Redmine API accepts both numeric IDs and issue keys in the URL
        url = f"{self.endpoint}/issues/{issue_identifier}.json"
        
        data = {
            "issue": {
                "notes": comment,
                "private_notes": notes_private
            }
        }
        
        response = self.session.put(url, json=data)
        response.raise_for_status()
        # Redmine may return empty response for successful PUT requests
        if response.text.strip():
            return response.json()
        return {"status": "success", "message": "Comment added successfully"}
    
    def report_activity(self, issue_identifier: str, hours: float, activity_id: int,
                       comment: Optional[str] = None, 
                       time_entry_comment: Optional[str] = None,
                       spent_on: Optional[str] = None,
                       notes_private: bool = False) -> dict:
        """
        Report activity: log time and optionally add a comment.
        
        Args:
            issue_identifier: The issue ID (numeric) or issue key (e.g., ISSUEKEY-1)
            hours: Number of hours to log
            activity_id: Activity type ID
            comment: Comment to add to the issue (optional)
            time_entry_comment: Comment for the time entry itself (optional)
            spent_on: Date in YYYY-MM-DD format (defaults to today)
            notes_private: If True, adds a private note (requires permissions)
        
        Returns:
            dict: Combined results from time logging and comment addition
        """
        results = {}
        
        # Log time
        try:
            time_result = self.log_time(
                issue_identifier=issue_identifier,
                hours=hours,
                activity_id=activity_id,
                comments=time_entry_comment,
                spent_on=spent_on
            )
            results['time_entry'] = time_result
            print(f"✓ Successfully logged {hours} hours to issue {issue_identifier}")
        except requests.exceptions.RequestException as e:
            results['time_entry_error'] = str(e)
            print(f"✗ Failed to log time: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                if hasattr(e.response, 'text'):
                    print(f"  Response: {e.response.text}", file=sys.stderr)
        
        # Add comment if provided
        if comment:
            try:
                comment_result = self.add_comment(
                    issue_identifier=issue_identifier,
                    comment=comment,
                    notes_private=notes_private
                )
                results['comment'] = comment_result
                print(f"✓ Successfully added comment to issue {issue_identifier}")
            except requests.exceptions.RequestException as e:
                results['comment_error'] = str(e)
                print(f"✗ Failed to add comment: {e}", file=sys.stderr)
                if hasattr(e, 'response') and e.response is not None:
                    if hasattr(e.response, 'text'):
                        print(f"  Response: {e.response.text}", file=sys.stderr)
        
        return results


def get_activity_id_mapping():
    """Return common activity ID mappings for reference."""
    return {
        "Design": 9,
        "Development": 8,
        "Documentation": 10,
        "Management": 11,
        "Support": 12,
        "Testing": 13
    }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Report activity to Redmine (log time and add comments)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Log 2 hours of development work with a comment (using numeric ID)
  python redmine_activity_reporter.py --issue 123 --hours 2 --activity-id 8 --comment "Fixed bug in login module"

  # Log time using issue key (e.g., ISSUEKEY-1)
  python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 2 --activity-id 8 --comment "Fixed bug in login module"

  # Log time only (no comment)
  python redmine_activity_reporter.py --issue 123 --hours 1.5 --activity-id 8

  # Log time with time entry comment but no issue comment
  python redmine_activity_reporter.py --issue 123 --hours 2 --activity-id 8 --time-comment "Worked on API integration"

Environment Variables:
  REDMINE_ENDPOINT: Redmine base URL (e.g., https://redmine.example.com)
  REDMINE_API_KEY: Redmine API key for authentication

Common Activity IDs:
  Development: 8
  Design: 9
  Documentation: 10
  Management: 11
  Support: 12
  Testing: 13
        """
    )
    
    parser.add_argument(
        '--issue', '-i',
        type=str,
        required=True,
        help='Issue ID (numeric) or issue key (e.g., ISSUEKEY-1) to report activity for'
    )
    
    parser.add_argument(
        '--hours',
        type=float,
        required=True,
        help='Number of hours to log'
    )
    
    parser.add_argument(
        '--activity-id', '-a',
        type=int,
        required=True,
        help='Activity type ID (e.g., 8 for Development)'
    )
    
    parser.add_argument(
        '--comment', '-c',
        type=str,
        help='Comment to add to the issue'
    )
    
    parser.add_argument(
        '--time-comment',
        type=str,
        help='Comment for the time entry itself'
    )
    
    parser.add_argument(
        '--spent-on',
        type=str,
        help='Date in YYYY-MM-DD format (defaults to today)'
    )
    
    parser.add_argument(
        '--private',
        action='store_true',
        help='Add comment as private note (requires permissions)'
    )
    
    parser.add_argument(
        '--endpoint',
        type=str,
        help='Redmine endpoint URL (overrides REDMINE_ENDPOINT env var)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='Redmine API key (overrides REDMINE_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Get endpoint and API key from environment or arguments
    endpoint = args.endpoint or os.getenv('REDMINE_ENDPOINT')
    api_key = args.api_key or os.getenv('REDMINE_API_KEY')
    
    if not endpoint:
        print("Error: REDMINE_ENDPOINT environment variable or --endpoint argument is required", 
              file=sys.stderr)
        sys.exit(1)
    
    if not api_key:
        print("Error: REDMINE_API_KEY environment variable or --api-key argument is required", 
              file=sys.stderr)
        sys.exit(1)
    
    # Create reporter and report activity
    reporter = RedmineActivityReporter(endpoint, api_key)
    
    try:
        results = reporter.report_activity(
            issue_identifier=args.issue,
            hours=args.hours,
            activity_id=args.activity_id,
            comment=args.comment,
            time_entry_comment=args.time_comment,
            spent_on=args.spent_on,
            notes_private=args.private
        )
        
        # Exit with error code if any operation failed
        if 'time_entry_error' in results or 'comment_error' in results:
            sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

