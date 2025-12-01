#!/usr/bin/env python3
"""
Update README.md with translation status report.

This script reads a markdown status report and updates the README.md file,
replacing the content under the "## Translation status" section.
"""

import argparse
import sys
import re
from pathlib import Path


def read_file(file_path: str) -> str:
    """Read file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def write_file(file_path: str, content: str):
    """Write content to file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)
        sys.exit(1)


def update_readme_section(readme_content: str, status_content: str) -> str:
    """
    Update the "## Translation status" section in README.md.
    
    Args:
        readme_content: Current README.md content
        status_content: New status report content to insert
    
    Returns:
        Updated README.md content
    """
    # Pattern to match the "## Translation status" section
    # Matches from "## Translation status" to the next "##" or end of file
    pattern = r'(## Translation status\s*\n)(.*?)(?=\n## |\Z)'
    
    # Check if section exists
    match = re.search(pattern, readme_content, re.DOTALL)
    
    if match:
        # Section exists, replace its content
        header = match.group(1)
        # Add the status content with proper spacing
        new_section = header + status_content.rstrip() + "\n"
        # Replace the entire section
        updated_content = re.sub(pattern, new_section, readme_content, flags=re.DOTALL)
    else:
        # Section doesn't exist, append it at the end
        # Ensure there's a newline before adding the section
        if not readme_content.endswith('\n'):
            readme_content += '\n'
        updated_content = readme_content + "\n## Translation status\n\n" + status_content.rstrip() + "\n"
    
    return updated_content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update README.md with translation status report',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--readme',
        type=str,
        required=True,
        help='Path to README.md file'
    )
    
    parser.add_argument(
        '--status',
        type=str,
        required=True,
        help='Path to markdown status report file'
    )
    
    args = parser.parse_args()
    
    # Read files
    readme_content = read_file(args.readme)
    status_content = read_file(args.status)
    
    # Update README
    updated_content = update_readme_section(readme_content, status_content)
    
    # Write back to README
    write_file(args.readme, updated_content)
    
    print(f"Updated {args.readme} with translation status", file=sys.stderr)


if __name__ == '__main__':
    main()
