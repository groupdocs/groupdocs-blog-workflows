# Blog Post Translator

Translates blog posts to 21 languages using LLM with optimized prompts, structural validation, and optional cross-model quality review.

## Architecture

```
                     ┌─────────────────────┐
                     │  Translation Report  │
                     │  (from scanner or    │
                     │   validator)         │
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │  For each post/lang  │
                     └──────────┬──────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │  1. Translate front-matter (batch) │
              │     JSON batch → 1 API call        │
              │  2. Translate body                 │
              │     Optimized minimal prompt       │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │  3. Structural checks (no LLM)    │
              │     code blocks, headers,          │
              │     shortcodes, link refs,          │
              │     product names, length           │
              ├────── issues? ─────────────────────┤
              │  yes → retry with feedback         │
              │  no  ↓                             │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │  4. LLM review (optional)         │
              │     Cross-model quality check      │
              │     (reviewer_model ≠ translator)  │
              ├────── issues? ─────────────────────┤
              │  yes → retry with reviewer feedback│
              │  no  ↓                             │
              └─────────────────┬─────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │  5. Save & verify                  │
              │     Front-matter + headers checked │
              └───────────────────────────────────┘
```

Each retry includes specific feedback from the previous attempt, so the translator knows exactly what to fix.

## Prompt design

The prompts were optimized through 22 automated experiments using the [autoresearch pattern](https://github.com/karpathy/autoresearch). Key findings:

- **Shorter prompts beat verbose ones** for long documents — frees output tokens for the actual translation
- **Explicit product name glossary** was the single biggest quality improvement
- **Hugo shortcodes and link references** need explicit "copy verbatim" rules
- **Temperature 0.1** produces the most consistent output
- **Batch JSON front-matter** reduces API calls from ~7 to 2 per language

## Setup

```bash
pip install -r requirements.txt
```

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROFESSIONALIZE_API_KEY` | Yes | — | API key for LLM service |
| `PROFESSIONALIZE_API_URL` | No | `https://llm.professionalize.com/v1` | API endpoint |
| `PROFESSIONALIZE_MODEL_NAME` | No | `recommended` | Model for translation |
| `PROFESSIONALIZE_REVIEWER_MODEL` | No | None (disabled) | Model for cross-model review |

When `PROFESSIONALIZE_REVIEWER_MODEL` is set, each translation gets reviewed by a second model. If the reviewer finds issues, the translator retries with the reviewer's feedback included in the prompt. Without it, only structural checks and basic verification run.

## Usage

```bash
# Translate all missing posts from a report
python translate_posts.py translation_status.json

# Translate 1 post with verbose output
python translate_posts.py translation_status.json --limit 1 --verbose

# Translate only Arabic
python translate_posts.py translation_status.json --lang ar

# Translate specific post
python translate_posts.py translation_status.json --post "2025-10-23-groupdocs-watermark"

# Preview without translating
python translate_posts.py translation_status.json --dry-run

# Custom retry count
python translate_posts.py translation_status.json --retries 5 --verbose
```

## Input format

Accepts JSON reports from either the **missing-translations-scanner** or the **translation-validator**. Both produce the same schema:

```json
{
  "posts": [
    {
      "path": "content/Groupdocs.Blog/category/post-name",
      "missing_languages": ["ar", "de", "ja"]
    }
  ]
}
```

## Output

Translated posts are saved as `index.{lang}.md` in the post directory:

```
content/Groupdocs.Blog/category/post-name/
  ├── index.md          (English - original)
  ├── index.ar.md       (Arabic - translated)
  ├── index.de.md       (German - translated)
  └── ...
```

## Supported languages (21)

ar (Arabic), cs (Czech), de (German), es (Spanish), fa (Persian), fr (French), he (Hebrew), id (Indonesian), it (Italian), ja (Japanese), ko (Korean), nl (Dutch), pl (Polish), pt (Portuguese), ru (Russian), th (Thai), tr (Turkish), uk (Ukrainian), vi (Vietnamese), zh (Chinese Simplified), zh-hant (Chinese Traditional)
