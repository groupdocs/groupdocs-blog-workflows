#!/usr/bin/env python3
"""
Create a formatted comment for Redmine about release post draft creation.

This script reads the generated draft index.md file and creates a formatted comment
that can be used with redmine-activity-reporter.
"""

import sys
import argparse
import os
import re

try:
    import yaml
except ImportError:
    # Try pyyaml as alternative import name
    try:
        import yaml as yaml
    except ImportError:
        print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)


def extract_post_info(index_md_path: str) -> dict:
    """
    Extract post title and URL from the generated index.md file.
    
    Args:
        index_md_path: Path to the generated index.md file
    
    Returns:
        Dictionary with 'title' and 'url' keys
    """
    try:
        with open(index_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract front-matter (between --- markers)
        if not content.startswith('---'):
            return {'title': '', 'url': ''}
        
        # Find the end of front-matter
        end_marker = content.find('\n---', 4)  # Skip first ---
        if end_marker == -1:
            return {'title': '', 'url': ''}
        
        front_matter = content[4:end_marker]  # Skip first ---\n
        
        # Parse YAML front-matter
        try:
            front_matter_data = yaml.safe_load(front_matter)
            title = front_matter_data.get('title', '')
            url_path = front_matter_data.get('url', '')
            
            # Construct full URL
            base_url = 'https://blog.groupdocs.com'
            if url_path:
                url = base_url + url_path.rstrip('/')
            else:
                url = ''
            
            return {'title': title, 'url': url}
        except Exception:
            return {'title': '', 'url': ''}
    except FileNotFoundError:
        print(f"Error: Draft file not found: {index_md_path}", file=sys.stderr)
        return {'title': '', 'url': ''}
    except Exception as e:
        print(f"Error reading draft file: {e}", file=sys.stderr)
        return {'title': '', 'url': ''}


def create_redmine_comment(
    product_name: str,
    version: str,
    post_title: str,
    post_url: str,
    user_mention: str = None,
    action_url: str = None
) -> str:
    """
    Create formatted comment for Redmine.
    
    Args:
        product_name: Full product name (e.g., "GroupDocs.Viewer for .NET")
        version: Product version (e.g., "25.12")
        post_title: Blog post title
        post_url: Blog post URL
        user_mention: Optional user mention to include at the beginning (e.g., "@username")
        action_url: Optional Job URL to include at the end
    
    Returns:
        Formatted comment text
    """
    comment = ""
    
    # Add user mention if provided
    if user_mention:
        comment += f"{user_mention}\n\n"
    
    # Main message with post link
    if post_url and post_title:
        comment += f"Created release post draft for {product_name} v{version}: [{post_title}]({post_url})\n"
    else:
        comment += f"Created release post draft for {product_name} v{version}\n"
    
    # Add action URL if provided
    if action_url:
        comment += f"\nJob: {action_url}\n"
    
    comment += "\n---"
    
    return comment


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create Redmine comment for release post draft',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--index-md',
        type=str,
        required=True,
        help='Path to generated index.md file'
    )
    
    parser.add_argument(
        '--product-name',
        type=str,
        required=True,
        help='Full product name (e.g., "GroupDocs.Viewer for .NET")'
    )
    
    parser.add_argument(
        '--version',
        type=str,
        required=True,
        help='Product version (e.g., "25.12")'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='-',
        help='Output file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Extract post info from index.md
    post_info = extract_post_info(args.index_md)
    post_title = post_info.get('title', '')
    post_url = post_info.get('url', '')
    
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
    comment = create_redmine_comment(
        product_name=args.product_name,
        version=args.version,
        post_title=post_title,
        post_url=post_url,
        user_mention=user_mention,
        action_url=action_url
    )
    
    # Output comment
    if args.output == '-':
        print(comment)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(comment)


if __name__ == '__main__':
    main()
