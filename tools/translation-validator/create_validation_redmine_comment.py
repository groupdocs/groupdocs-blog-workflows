#!/usr/bin/env python3
"""
Create Redmine comment from translation validation report.

Lists posts flagged for retranslation with their issues.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Create Redmine comment from validation report')
    parser.add_argument('--report-json', required=True, help='Path to validation_report.json')
    parser.add_argument('--output', required=True, help='Output file for Redmine comment')
    args = parser.parse_args()

    with open(args.report_json, 'r', encoding='utf-8') as f:
        report = json.load(f)

    summary = report.get('summary', {})
    posts = report.get('posts', [])

    report_to_user = os.getenv('REDMINE_REPORT_TO_USER', '')
    job_url = os.getenv('GITHUB_SERVER_URL', 'https://github.com')
    job_url += f"/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"

    lines = []
    if report_to_user:
        lines.append(f"@{report_to_user}")
        lines.append("")

    lines.append("### Translation Quality Validation Report")
    lines.append("")
    lines.append(f"- Posts scanned: {summary.get('total_posts_scanned', 0)}")
    lines.append(f"- Translations checked: {summary.get('total_translations_checked', 0)}")
    lines.append(f"- Valid: {summary.get('valid_translations', 0)}")
    lines.append(f"- Invalid (flagged for retranslation): {summary.get('invalid_translations', 0)}")
    lines.append(f"- Posts needing retranslation: {summary.get('posts_needing_retranslation', 0)}")
    lines.append("")

    # Issues breakdown
    issues = summary.get('issues_breakdown', {})
    if issues:
        lines.append("#### Issues found")
        lines.append("")
        for issue, count in sorted(issues.items(), key=lambda x: -x[1]):
            lines.append(f"- `{issue}`: {count}")
        lines.append("")

    # Posts to retranslate
    if posts:
        lines.append("#### Posts flagged for retranslation")
        lines.append("")
        for post in posts:
            post_name = Path(post['path']).name
            langs = ', '.join(post['missing_languages'])
            lang_count = len(post['missing_languages'])
            lines.append(f"- **{post_name}** ({lang_count} languages): {langs}")
        lines.append("")

    lines.append(f"[View workflow run]({job_url})")

    comment = '\n'.join(lines)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(comment)

    print(f"Redmine comment saved to {args.output}")
    print(f"Posts flagged: {len(posts)}")


if __name__ == '__main__':
    main()
