# Missing Translations Scanner

Scans all blog post directories and identifies posts that are missing translation files.

## What it does

- Finds all blog post directories containing `index.md`
- Reads expected languages from `config.yml`
- Checks for `index.{lang}.md` files for each language
- Reports which posts are missing which translations
- Filters out archived posts (`zArchive` tag) and posts published before 2024-07-01

This tool checks for **file existence only** — it does not validate translation quality. Use the **translation-validator** for quality checks.

## Usage

```bash
# Basic scan
python scan_missing_translations.py --content content --config config.yml

# Save JSON report for the translator
python scan_missing_translations.py --content content --config config.yml --output report.json

# Verbose output
python scan_missing_translations.py --content content --config config.yml --verbose
```

## Output format

The JSON report is consumed directly by `translate_posts.py`:

```json
{
  "summary": {
    "total_posts_scanned": 99,
    "posts_with_missing_translations": 5,
    "posts_complete": 94,
    "expected_languages": ["ar", "cs", "de", ...],
    "all_complete": false
  },
  "posts": [
    {
      "path": "content/Groupdocs.Blog/category/post-name",
      "url": "https://blog.groupdocs.com/category/post-name/",
      "missing_languages": ["zh-hant", "th"],
      "missing_count": 2,
      "total_expected": 21
    }
  ]
}
```

## Filters

| Filter | What it skips | Default |
|--------|--------------|---------|
| `archived` | Posts with `zArchive` tag | Enabled |
| `date_range` | Posts before `min_date` (YYYY-MM-DD) or `min_year` | `min_date=2024-07-01` |

## Exit codes

- `0` — always (allows workflows to continue)

## Requirements

- Python 3.6+
- `pyyaml>=5.4.1`
