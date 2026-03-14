# Blog Workflow Tools

Automation tools for the GroupDocs blog translation and publishing pipeline.

## Translation pipeline

Three tools work together to keep blog posts translated across 21 languages:

```
┌─────────────────────────┐     ┌──────────────────────────┐
│  missing-translations-  │     │  translation-validator   │
│  scanner                │     │                          │
│                         │     │  Checks quality of       │
│  Finds posts without    │     │  existing translations   │
│  translation files      │     │  (structural + content)  │
│                         │     │                          │
│  Schedule: daily 6:00AM │     │  Schedule: weekly Sunday │
└───────────┬─────────────┘     └────────────┬─────────────┘
            │                                │
            │  report.json                   │  retranslate.json
            │  (missing files)               │  (bad quality)
            │                                │
            └──────────┬─────────────────────┘
                       │
            ┌──────────▼──────────┐
            │  blog-post-         │
            │  translator         │
            │                     │
            │  Translates posts   │
            │  with optimized     │
            │  prompts + review   │
            │                     │
            │  Schedule: daily    │
            │  6:10AM (new posts) │
            │  + weekly (fixes)   │
            └─────────────────────┘
```

### Daily flow (new translations)

1. **6:00 AM** — Scanner finds posts missing translation files → `translations_scan_report.json`
2. **6:10 AM** — Translator picks up the report, translates 1 post to all missing languages
3. Commits to blog repo, deploys to QA and production, logs to Redmine

### Weekly flow (quality fixes)

1. **Sunday 7:00 AM** — Validator checks all existing translations against English originals
2. Flags posts with structural issues (broken shortcodes, missing headers, truncation)
3. Logs validation results to Redmine
4. Translator retranslates all flagged posts with optimized prompts
5. Commits fixes, deploys, logs retranslation to Redmine

## Tools

| Tool | Purpose | Schedule | Input | Output |
|------|---------|----------|-------|--------|
| [missing-translations-scanner](missing-translations-scanner/) | Find posts without translation files | Daily 6:00 AM | Blog content dir | `report.json` |
| [blog-post-translator](blog-post-translator/) | Translate posts using LLM | Daily 6:10 AM + weekly | `report.json` | `index.{lang}.md` files |
| [translation-validator](translation-validator/) | Check quality of existing translations | Weekly Sunday | Blog content dir | `retranslate.json` |
| [redmine-activity-reporter](redmine-activity-reporter/) | Log time and comments to Redmine | Used by other tools | API calls | Redmine entries |
| [public-release-post-draft](public-release-post-draft/) | Generate release post drafts | On demand | Release data | Draft markdown |
| [public-release-post-cover](public-release-post-cover/) | Generate cover images for posts | On demand | Post metadata | Cover images |
| [update-workflow-defaults](update-workflow-defaults/) | Update workflow configuration | On demand | Config changes | Updated workflows |

## Translation quality approach

The translation prompts were optimized through 22 automated experiments using the [autoresearch pattern](https://github.com/karpathy/autoresearch) — an iterative loop of modify, measure, keep/revert. Key results:

- **Optimized minimal prompts** beat verbose instructions for long documents
- **Cross-model review** (translator model + separate reviewer model) catches issues that same-model evaluation misses
- **Structural checks** (code blocks, shortcodes, headers, links) catch 87% of translation issues without any LLM call
- **Temperature 0.1** produces the most consistent translations

### Translation flow per post

1. **Translate** front-matter as JSON batch (1 call) + body (1 call) using gpt-oss
2. **Structural check** (free) — code blocks, headers, shortcodes, link refs, product names, length
3. **LLM review** (optional, 1 call) — cross-model quality check using qwen3-next
4. **Retry with feedback** if issues found — the retry prompt includes specific issues from the prior attempt
5. **Save and verify** — check front-matter and headers are actually translated

## Supported languages (21)

ar (Arabic), cs (Czech), de (German), es (Spanish), fa (Persian), fr (French), he (Hebrew), id (Indonesian), it (Italian), ja (Japanese), ko (Korean), nl (Dutch), pl (Polish), pt (Portuguese), ru (Russian), th (Thai), tr (Turkish), uk (Ukrainian), vi (Vietnamese), zh (Chinese Simplified), zh-hant (Chinese Traditional)

## Shared configuration

All tools use these environment variables:

| Variable | Used by | Description |
|----------|---------|-------------|
| `PROFESSIONALIZE_API_KEY` | translator | LLM API key |
| `PROFESSIONALIZE_API_URL` | translator | LLM API endpoint |
| `PROFESSIONALIZE_MODEL_NAME` | translator | Translation model |
| `PROFESSIONALIZE_REVIEWER_MODEL` | translator | Review model (optional) |
| `REDMINE_ENDPOINT` | redmine reporter | Redmine base URL |
| `REDMINE_API_KEY` | redmine reporter | Redmine API key |
| `REDMINE_ISSUE_ID` | redmine reporter | Issue to log to |
| `REDMINE_ACTIVITY_ID` | redmine reporter | Activity type ID |
