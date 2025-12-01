#!/usr/bin/env python3
"""
Blog Post Translator

Reads translation status report and translates missing blog posts using LLM.
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI


def create_client() -> OpenAI:
    """Create OpenAI client from environment variables."""
    api_key = os.getenv("PROFESSIONALIZE_API_KEY")
    base_url = os.getenv("PROFESSIONALIZE_API_URL", "https://llm.professionalize.com/v1")
    if not api_key:
        raise SystemExit("Missing environment variable: PROFESSIONALIZE_API_KEY")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_model_name() -> str:
    """Get model name from environment variable."""
    return os.getenv("MODEL_NAME", "gpt-oss")


def load_translation_report(report_path: str) -> Dict:
    """Load translation status report."""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Report file not found: {report_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse report file: {e}")
        sys.exit(1)


def read_post_file(post_path: str) -> Optional[str]:
    """Read blog post markdown file."""
    post_file = Path(post_path) / 'index.md'
    
    if not post_file.exists():
        print(f"Warning: Post file not found: {post_file}")
        return None
    
    try:
        with open(post_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading post file {post_file}: {e}")
        return None


def parse_front_matter(content: str):
    """
    Parse front-matter from markdown content.
    
    Returns:
        Tuple of (front_matter_dict, content_body)
    """
    if not content.startswith('---'):
        return None, content
    
    # Find the end of front-matter
    end_marker = content.find('\n---', 4)  # Skip first ---
    if end_marker == -1:
        return None, content
    
    front_matter_text = content[4:end_marker]  # Skip first ---\n
    content_body = content[end_marker + 5:].lstrip()  # Skip \n---\n
    
    try:
        front_matter = yaml.safe_load(front_matter_text)
        return front_matter, content_body
    except Exception as e:
        print(f"Warning: Failed to parse front-matter: {e}")
        return None, content


def translate_text(client: OpenAI, model: str, text: str, target_lang: str, context: str = "") -> Optional[str]:
    """
    Translate text using LLM.
    
    Args:
        client: OpenAI client
        model: Model name
        text: Text to translate
        target_lang: Target language code
        context: Additional context for translation
    
    Returns:
        Translated text or None if translation fails
    """
    # Language name mapping
    lang_names = {
        'ar': 'Arabic', 'cs': 'Czech', 'de': 'German', 'es': 'Spanish',
        'fa': 'Persian/Farsi', 'fr': 'French', 'he': 'Hebrew', 'id': 'Indonesian',
        'it': 'Italian', 'ja': 'Japanese', 'ko': 'Korean', 'nl': 'Dutch',
        'pl': 'Polish', 'pt': 'Portuguese', 'ru': 'Russian', 'th': 'Thai',
        'tr': 'Turkish', 'uk': 'Ukrainian', 'vi': 'Vietnamese',
        'zh': 'Chinese (Simplified)', 'zh-hant': 'Chinese (Traditional)'
    }
    
    target_lang_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""Translate the following text to {target_lang_name}. 
{context}
Preserve all markdown formatting, code blocks, links, and special characters exactly as they are.
Only translate the text content, not the markdown syntax or URLs.

Text to translate:
{text}"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a professional translator specializing in technical documentation. Translate content to {target_lang_name} while preserving all formatting, code, and links."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error translating text: {e}")
        return None


def update_url_for_language(url: str, lang_code: str) -> str:
    """
    Update URL to include language prefix.
    
    Args:
        url: Original URL (e.g., "/comparison/groupdocs-comparison-for-net-25-8/")
        lang_code: Language code (e.g., "ar")
    
    Returns:
        URL with language prefix (e.g., "/ar/comparison/groupdocs-comparison-for-net-25-8/")
    """
    if lang_code == 'en':
        return url
    
    # Remove leading slash if present, add language prefix
    url_clean = url.lstrip('/')
    return f"/{lang_code}/{url_clean}"


def translate_front_matter(client: OpenAI, model: str, front_matter: Dict, lang_code: str) -> Dict:
    """
    Translate front-matter fields.
    
    Args:
        client: OpenAI client
        model: Model name
        front_matter: Original front-matter dictionary
        lang_code: Target language code
    
    Returns:
        Translated front-matter dictionary
    """
    translated = front_matter.copy()
    
    # Fields to translate
    fields_to_translate = ['title', 'seoTitle', 'description', 'summary']
    
    for field in fields_to_translate:
        if field in translated and translated[field]:
            translated_text = translate_text(
                client, model, translated[field], lang_code,
                context=f"This is a {field} field for a technical blog post."
            )
            if translated_text:
                translated[field] = translated_text
    
    # Translate cover fields if present
    if 'cover' in translated and isinstance(translated['cover'], dict):
        cover = translated['cover']
        if 'alt' in cover and cover['alt']:
            alt_text = translate_text(
                client, model, cover['alt'], lang_code,
                context="This is an alt text for an image in a technical blog post."
            )
            if alt_text:
                cover['alt'] = alt_text
        
        if 'caption' in cover and cover['caption']:
            caption_text = translate_text(
                client, model, cover['caption'], lang_code,
                context="This is a caption for an image in a technical blog post."
            )
            if caption_text:
                cover['caption'] = caption_text
    
    # Update URL for language
    if 'url' in translated:
        translated['url'] = update_url_for_language(translated['url'], lang_code)
    
    # Translate author name if it's a common name (optional - can be skipped)
    # For now, we'll keep author as is since it might be a proper name
    
    return translated


def save_translated_post(post_path: str, lang_code: str, front_matter: Dict, content: str):
    """
    Save translated post to file.
    
    Args:
        post_path: Path to post directory
        lang_code: Language code
        front_matter: Translated front-matter dictionary
        content: Translated content body
    """
    post_dir = Path(post_path)
    output_file = post_dir / f'index.{lang_code}.md'
    
    # Convert front-matter to YAML
    front_matter_yaml = yaml.dump(
        front_matter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )
    
    # Combine front-matter and content
    full_content = f"---\n{front_matter_yaml}---\n\n{content}"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        return True
    except Exception as e:
        print(f"Error saving translated post to {output_file}: {e}")
        return False


def translate_post(
    client: OpenAI,
    model: str,
    post_path: str,
    lang_code: str,
    verbose: bool = False
) -> bool:
    """
    Translate a single blog post to target language.
    
    Args:
        client: OpenAI client
        model: Model name
        post_path: Path to post directory
        lang_code: Target language code
        verbose: Enable verbose output
    
    Returns:
        True if translation succeeded, False otherwise
    """
    if verbose:
        print(f"Translating {post_path} to {lang_code}...")
    
    # Read English post
    content = read_post_file(post_path)
    if not content:
        return False
    
    # Parse front-matter and content
    front_matter, content_body = parse_front_matter(content)
    if not front_matter:
        print(f"Warning: Could not parse front-matter for {post_path}")
        return False
    
    # Translate front-matter
    translated_front_matter = translate_front_matter(client, model, front_matter, lang_code)
    
    # Translate content body
    translated_content = translate_text(
        client, model, content_body, lang_code,
        context="This is the main content of a technical blog post. Preserve all markdown formatting, code blocks, and links."
    )
    
    if not translated_content:
        print(f"Error: Failed to translate content for {post_path} ({lang_code})")
        return False
    
    # Save translated post
    success = save_translated_post(post_path, lang_code, translated_front_matter, translated_content)
    
    if verbose and success:
        print(f"✓ Successfully translated {post_path} to {lang_code}")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Translate blog posts using LLM based on translation status report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python translate_posts.py translation_status.json
  python translate_posts.py translation_status.json --lang ar
  python translate_posts.py translation_status.json --post "content/Groupdocs.Blog/comparison/2025-09-01-groupdocs-comparison-for-net-25-8"
  python translate_posts.py translation_status.json --limit 5 --verbose
        """
    )
    
    parser.add_argument(
        'report',
        type=str,
        help='Path to translation status JSON report'
    )
    
    parser.add_argument(
        '--lang',
        type=str,
        default=None,
        help='Translate only to specific language code (e.g., ar, de, fr)'
    )
    
    parser.add_argument(
        '--post',
        type=str,
        default=None,
        help='Translate only specific post path'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of posts to translate'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - show what would be translated without actually translating'
    )
    
    args = parser.parse_args()
    
    # Load report
    report = load_translation_report(args.report)
    posts = report.get('posts', [])
    
    if not posts:
        print("No posts with missing translations found in report.")
        sys.exit(0)
    
    print(f"Found {len(posts)} posts with missing translations")
    
    # Filter posts if --post specified
    if args.post:
        posts = [p for p in posts if args.post in p.get('path', '')]
        if not posts:
            print(f"No post found matching: {args.post}")
            sys.exit(1)
        print(f"Filtered to 1 post: {args.post}")
    
    # Limit posts if --limit specified
    if args.limit:
        posts = posts[:args.limit]
        print(f"Limited to {len(posts)} posts")
    
    if args.dry_run:
        print("\n=== DRY RUN MODE ===")
        for post in posts:
            print(f"\nPost: {post['path']}")
            langs_to_translate = [args.lang] if args.lang and args.lang in post['missing_languages'] else post['missing_languages']
            print(f"Missing languages: {', '.join(langs_to_translate)}")
        sys.exit(0)
    
    # Initialize LLM client
    try:
        client = create_client()
        model = get_model_name()
    except SystemExit as e:
        print(e)
        sys.exit(1)
    
    # Process each post
    total_translated = 0
    total_failed = 0
    
    for post_idx, post in enumerate(posts, 1):
        post_path = post['path']
        missing_langs = post['missing_languages']
        
        # Filter languages if --lang specified
        if args.lang:
            if args.lang not in missing_langs:
                if args.verbose:
                    print(f"Skipping {post_path} - {args.lang} not in missing languages")
                continue
            missing_langs = [args.lang]
        
        print(f"\n[{post_idx}/{len(posts)}] Processing: {post_path}")
        print(f"Missing languages: {', '.join(missing_langs)}")
        
        for lang_idx, lang_code in enumerate(missing_langs, 1):
            print(f"  [{lang_idx}/{len(missing_langs)}] Translating to {lang_code}...", end=' ', flush=True)
            
            success = translate_post(client, model, post_path, lang_code, args.verbose)
            
            if success:
                print("✓")
                total_translated += 1
            else:
                print("✗")
                total_failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("TRANSLATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total translations completed: {total_translated}")
    print(f"Total translations failed: {total_failed}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()

