#!/usr/bin/env python3
"""
Create a simplified time entry comment for release post draft.

This script reads the generated draft index.md file and creates a simplified comment
containing just the post URL for time logging.
"""

import sys
import argparse

try:
    import yaml
except ImportError:
    # Try pyyaml as alternative import name
    try:
        import yaml as yaml
    except ImportError:
        print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)


def extract_post_url(index_md_path: str) -> str:
    """
    Extract post URL from the generated index.md file.
    
    Args:
        index_md_path: Path to the generated index.md file
    
    Returns:
        Post URL or empty string if not found
    """
    try:
        with open(index_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract front-matter (between --- markers)
        if not content.startswith('---'):
            return ''
        
        # Find the end of front-matter
        end_marker = content.find('\n---', 4)  # Skip first ---
        if end_marker == -1:
            return ''
        
        front_matter = content[4:end_marker]  # Skip first ---\n
        
        # Parse YAML front-matter
        try:
            front_matter_data = yaml.safe_load(front_matter)
            url_path = front_matter_data.get('url', '')
            
            # Construct full URL
            base_url = 'https://blog.groupdocs.com'
            if url_path:
                return base_url + url_path.rstrip('/')
            return ''
        except Exception:
            return ''
    except FileNotFoundError:
        print(f"Error: Draft file not found: {index_md_path}", file=sys.stderr)
        return ''
    except Exception as e:
        print(f"Error reading draft file: {e}", file=sys.stderr)
        return ''


def create_simplified_time_comment(post_url: str) -> str:
    """
    Create simplified time entry comment.
    
    Args:
        post_url: Blog post URL
    
    Returns:
        Simplified comment text
    """
    if post_url:
        return f"Created release blog post draft {post_url}"
    else:
        return "Created release blog post draft"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create simplified time comment for Redmine with post URL',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--index-md',
        type=str,
        required=True,
        help='Path to generated index.md file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='-',
        help='Output file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    # Extract post URL from index.md
    post_url = extract_post_url(args.index_md)
    
    # Create simplified comment
    comment = create_simplified_time_comment(post_url)
    
    # Output comment
    if args.output == '-':
        print(comment)
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(comment)


if __name__ == '__main__':
    main()
