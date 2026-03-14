# Translation Validator

Validates existing blog post translations and flags incomplete or incorrectly translated posts for retranslation.

Unlike the **missing-translations-scanner** (which finds posts without translation files), this tool checks the **quality** of existing translations by comparing them against the English original.

## What it checks

### Structural checks (programmatic, no LLM needed)

| Check | What it verifies | Fail threshold |
|-------|-----------------|----------------|
| Code blocks | Same number of code fences (```) | Difference > 2 |
| Headers | Same number of markdown headers | Difference > 2 |
| Tables | Table pipe counts match | Outside 70-130% |
| Length ratio | Translation length vs original | Outside 40-300% |
| Links | All URLs from original appear | Any missing |
| Product names | GroupDocs.*, .NET, NuGet preserved | >50% missing |
| Hugo shortcodes | `{{< figure ... >}}` copied verbatim | Any missing |
| Link references | `[N]: https://...` definitions preserved | Any missing |

### Content checks

| Check | What it verifies |
|-------|-----------------|
| Front-matter translated | title/description/summary differ from English |
| Headers translated | At least some markdown headers differ from English |
| Not truncated | Translation is at least 30% of original length |

## Usage

```bash
# Validate all translations (posts from 2025+)
python validate_translations.py --content content/Groupdocs.Blog

# Save report for retranslation
python validate_translations.py --content content/Groupdocs.Blog -o retranslate.json -v

# Check specific language
python validate_translations.py --content content/Groupdocs.Blog --lang de -v

# Check specific post
python validate_translations.py --content content/Groupdocs.Blog --post "watermark" -v

# Check older posts
python validate_translations.py --content content/Groupdocs.Blog --min-year 2024
```

## Integration with translator

The output JSON uses the same format as the missing-translations-scanner, so you can feed it directly to `translate_posts.py`:

```bash
# Step 1: Find bad translations
python validate_translations.py --content content/Groupdocs.Blog -o retranslate.json

# Step 2: Retranslate them
python translate_posts.py retranslate.json --verbose
```

## Supporting scripts

### create_validation_redmine_comment.py

Generates a Markdown-formatted Redmine comment from the validation report, listing flagged posts and issue breakdown.

```bash
python create_validation_redmine_comment.py --report-json validation_report.json --output comment.txt
```

## Exit codes

- `0` — all translations valid
- `1` — some translations need retranslation

## Requirements

- Python 3.6+
- `pyyaml>=6.0`
