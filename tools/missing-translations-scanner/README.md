# Blog Translation Scanner

A tool to scan blog posts in the `content` folder and identify missing translations.

## Overview

This scanner analyzes all blog post directories and checks which language translations are missing based on the languages configured in `config.yml`. It automatically filters out archived posts and posts published before 2025, focusing only on active content that needs translations.

## Features

- Automatically detects all blog post directories
- Reads expected languages from `config.yml`
- Identifies missing translations for each blog post
- Declarative filter system for excluding posts (archived, date range, etc.)
- Extracts URLs from blog post front-matter
- Produces human-readable text reports to console
- Can save JSON reports to file for programmatic use
- Includes filter information and generation timestamp in reports

## Usage

### Basic Usage

```bash
python scan_missing_translations.py
```

### With Verbose Output

```bash
python scan_missing_translations.py --verbose
```

### Save JSON Report to File

```bash
python scan_missing_translations.py --output translations_scan_report.json
```

### Custom Paths

```bash
python scan_missing_translations.py --content ../content --config ../config.yml
```

## Command Line Options

- `--content PATH`: Path to content directory (default: `content`)
- `--config PATH`: Path to config.yml file (default: `config.yml`)
- `--output PATH`: Save JSON report to file (optional, console always shows text report)
- `--verbose`: Enable verbose output during scanning
- `--help`: Show help message

## Expected File Structure

The scanner expects blog posts to be organized as:

```
content/
  Groupdocs.Blog/
    {category}/
      {post-name}/
        index.md          # English (default)
        index.ar.md       # Arabic
        index.cs.md       # Czech
        index.de.md       # German
        ...               # Other language files
```

## Output

The scanner produces a human-readable text report to the console by default. When `--output` is specified, it also saves a JSON report to the file.

### Text Report (Console)

The console output includes:
1. **Summary**: Date generated, total posts scanned, applied filters, filter counts, and translation status
2. **Detailed Report**: List of each blog post with its missing translations and URLs

#### Example Output

```
================================================================================
BLOG POST TRANSLATION SCANNER REPORT
================================================================================

SUMMARY
--------------------------------------------------------------------------------
Date generated: 2025-01-15 10:30:45 UTC
Total blog posts scanned: 43
Applied filters:
  - archived (tag=zArchive)
  - date_range (min_year=2025)

Posts filtered by filter:
  archived: 150
  date_range: 821

Posts with missing translations: 0
Posts with complete translations: 43
Expected languages: 21

✓ All blog posts have complete translations!
```

### JSON Report (File)

When `--output` is specified, a structured JSON report is saved to the file for programmatic use.

#### Example JSON Output

```json
{
  "summary": {
    "total_posts_scanned": 43,
    "posts_with_missing_translations": 0,
    "posts_complete": 43,
    "filters_applied": [
      {
        "name": "archived",
        "config": {
          "tag": "zArchive"
        }
      },
      {
        "name": "date_range",
        "config": {
          "min_year": 2025
        }
      }
    ],
    "filters_counts": {
      "archived": 150,
      "date_range": 821
    },
    "expected_languages": ["ar", "cs", "de", "es", "fa", "fr", "he", "id", "it", "ja", "ko", "nl", "pl", "pt", "ru", "th", "tr", "uk", "vi", "zh", "zh-hant"],
    "total_expected_languages": 21,
    "all_complete": true,
    "base_url": "https://blog.groupdocs.com/",
    "date_generated": "2025-01-15T10:30:45.123456+00:00"
  },
  "posts": [
    {
      "path": "content/Groupdocs.Blog/conversion/2024-01-15-example-post",
      "url": "https://blog.groupdocs.com/conversion/2024-01-15-example-post/",
      "urls": {
        "en": "https://blog.groupdocs.com/conversion/2024-01-15-example-post/",
        "ar": "https://blog.groupdocs.com/ar/conversion/2024-01-15-example-post/",
        "cs": "https://blog.groupdocs.com/cs/conversion/2024-01-15-example-post/",
        ...
      },
      "missing_languages": ["zh-hant", "th", "uk"],
      "missing_count": 3,
      "total_expected": 21
    }
  ]
}
```

#### JSON Structure

- `summary`: Overall statistics
  - `total_posts_scanned`: Total number of blog posts scanned (after filters)
  - `posts_with_missing_translations`: Number of posts missing at least one translation
  - `posts_complete`: Number of posts with all translations
  - `filters_applied`: Array of applied filters with their configurations
  - `filters_counts`: Object mapping filter names to number of posts filtered
  - `expected_languages`: Array of expected language codes
  - `total_expected_languages`: Count of expected languages
  - `all_complete`: Boolean indicating if all posts have complete translations
  - `base_url`: Base URL from config.yml (e.g., "https://blog.groupdocs.com/")
  - `date_generated`: ISO 8601 timestamp of when the report was generated
- `posts`: Array of posts with missing translations
  - `path`: Relative path to the blog post directory
  - `url`: Full URL for the English version of the post (from front-matter)
  - `urls`: Object mapping language codes to their full URLs (includes all expected languages)
  - `missing_languages`: Array of missing language codes
  - `missing_count`: Number of missing languages
  - `total_expected`: Total number of expected languages

## Filters

The scanner uses a declarative filter system to exclude certain posts from scanning:

### Default Filters

1. **Archived Posts**: Filters out posts with `zArchive` tag in front-matter
2. **Date Range**: Filters out posts published before 2025 (configurable via `min_year`)

Filters can be customized by modifying the `create_default_filters()` function in the code.

### Filter Types

- **`archived`**: Filters posts by tag (default: `zArchive`)
- **`date_range`**: Filters posts by publication year (`min_year`, `max_year`)
- **`tag`**: Generic tag-based filter

## Exit Codes

- `0`: Always exits successfully

The tool always exits with code 0 to allow automated workflows to continue execution and generate reports. Check the JSON report file or console output to determine if translations are missing.

## Requirements

- Python 3.6+
- PyYAML library

Install dependencies:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install pyyaml
```

## How It Works

1. **Configuration Loading**: Reads `config.yml` to get expected languages and base URL
2. **Post Discovery**: Recursively finds all directories containing `index.md` files
3. **Filtering**: Applies declarative filters to exclude archived or outdated posts
4. **Translation Detection**: Checks for `index.{lang}.md` files for each expected language
5. **URL Extraction**: Reads URLs from front-matter of markdown files
6. **Report Generation**: Creates text report for console and optional JSON report for file

## Notes

- URLs are extracted from the `url` field in each post's front-matter
- English posts use `index.md`, translations use `index.{lang}.md`
- Posts are filtered before translation checking
- The tool always exits with code 0 to allow automated workflows to continue and generate reports

