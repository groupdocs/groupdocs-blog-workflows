#!/usr/bin/env python3
"""
Update default values in create-release-post-draft.yml workflow file.

This script updates the version and title default values based on the current date.
"""

import re
import sys
from datetime import datetime
from pathlib import Path


def get_current_version_and_title():
    """Calculate current version and title based on current date."""
    now = datetime.now()
    year_short = str(now.year)[-2:]  # Last 2 digits of year
    month_num = now.month
    
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    month_name = month_names[month_num - 1]
    
    version = f"{year_short}.{month_num}"
    title = f"{month_name} {now.year} release"
    
    return version, title


def update_workflow_file(workflow_path: Path, new_version: str, new_title: str) -> bool:
    """
    Update the workflow file with new default values.
    
    Returns:
        True if changes were made, False otherwise
    """
    content = workflow_path.read_text(encoding='utf-8')
    original_content = content
    
    # Update version default (line with: default: "25.9")
    # Match the first occurrence of default: "YY.M" pattern (should be the version)
    version_pattern = r'(^\s+default:\s*")(\d{2}\.\d{1,2})(")'
    matches = list(re.finditer(version_pattern, content, re.MULTILINE))
    if matches:
        # Replace the first match (which should be the version default)
        match = matches[0]
        content = content[:match.start()] + match.group(1) + new_version + match.group(3) + content[match.end():]
    
    # Update title default (line with: default: "September 2025 release")
    # Match the first occurrence of default: "{Month} {Year} release" pattern (should be the title)
    title_pattern = r'(^\s+default:\s*")([A-Za-z]+ \d{4} release)(")'
    matches = list(re.finditer(title_pattern, content, re.MULTILINE))
    if matches:
        # Replace the first match (which should be the title default)
        match = matches[0]
        content = content[:match.start()] + match.group(1) + new_title + match.group(3) + content[match.end():]
    
    if content != original_content:
        workflow_path.write_text(content, encoding='utf-8')
        return True
    return False


def main():
    """Main entry point."""
    # Get current date-based values
    version, title = get_current_version_and_title()
    
    # Path to workflow file
    repo_root = Path(__file__).parent.parent.parent
    workflow_file = repo_root / ".github" / "workflows" / "create-release-post-draft.yml"
    
    if not workflow_file.exists():
        print(f"Error: Workflow file not found: {workflow_file}", file=sys.stderr)
        sys.exit(1)
    
    # Update the file
    changed = update_workflow_file(workflow_file, version, title)
    
    if changed:
        print(f"Updated version default to: {version}")
        print(f"Updated title default to: {title}")
        sys.exit(0)
    else:
        print("No changes needed - values are already up to date")
        sys.exit(0)


if __name__ == "__main__":
    main()
