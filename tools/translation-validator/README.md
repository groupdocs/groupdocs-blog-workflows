# Translation Validator

Scans existing blog post translations and identifies incomplete or incorrectly translated posts for retranslation.

Unlike the **missing-translations-scanner** (which finds posts without translation files), this tool checks the **quality** of existing translations by comparing them against the English original.

## What it checks

### Structural checks (programmatic, no LLM needed)
| Check | What it verifies |
|-------|-----------------|
| Links | All URLs from the original appear in the translation |
| Code blocks | Same number of code fences (```) |
| Headers | Same number of markdown headers |
| Tables | Table pipe counts match (within 30%) |
| Length ratio | Translation length is 40-300% of original |
| Product names | GroupDocs.*, .NET, NuGet appear in translation |
| Hugo shortcodes | `{{< figure ... >}}` copied verbatim |
| Link references | `[N]: https://...` definitions preserved |

### Content checks
| Check | What it verifies |
|-------|-----------------|
| Front-matter translated | title/description/summary differ from English |
| Headers translated | Markdown headers differ from English |
| Not truncated | Translation is at least 30% of original length |

## Usage

```bash
# Validate all translations (posts from 2025+)
python validate_translations.py --content content/Groupdocs.Blog

# Validate and save report for retranslation
python validate_translations.py --content content/Groupdocs.Blog -o retranslate.json -v

# Check specific language
python validate_translations.py --content content/Groupdocs.Blog --lang de -v

# Check specific post
python validate_translations.py --content content/Groupdocs.Blog --post "watermark" -v
```

## Integration with translator

The output JSON uses the same format as the missing-translations-scanner, so you can feed it directly to `translate_posts.py`:

```bash
# Step 1: Find bad translations
python validate_translations.py --content content/Groupdocs.Blog -o retranslate.json

# Step 2: Retranslate them
python translate_posts.py retranslate.json --verbose
```

## Exit codes

- `0` — all translations valid
- `1` — some translations need retranslation (report generated)
