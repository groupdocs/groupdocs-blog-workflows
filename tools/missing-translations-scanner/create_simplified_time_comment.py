#!/usr/bin/env python3
"""
Create a simplified time entry comment from translation scan report.

This script reads the translations_scan_report.json file and creates a simplified comment
containing just a summary for time logging.
"""

import json
import sys
import argparse


def create_simplified_time_comment(report: dict) -> str:
    """
    Create simplified time entry comment.
    
    Args:
        report: Translation scan report dictionary
    
    Returns:
        Simplified comment text
    """
    summary = report.get('summary', {})
    posts_with_missing = summary.get('posts_with_missing_translations', 0)
    
    if posts_with_missing == 0:
        return "Reviewed blog posts for missing translations. All blog posts have complete translations."
    elif posts_with_missing == 1:
        return "Reviewed blog posts for missing translations. Found 1 untranslated blog post."
    else:
        return f"Reviewed blog posts for missing translations. Found {posts_with_missing} untranslated blog posts."


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create simplified time comment for Redmine with scan summary',
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
    
    # Create simplified comment
    comment = create_simplified_time_comment(report)
    
    # Output comment
    if args.output == '-':
        print(comment)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(comment)


if __name__ == '__main__':
    main()
