# GroupDocs Blog Workflows

GitHub Actions and tools that support GroupDocs blog publishing.

## Create release cover image

- Run the Actions workflow "Create release post cover image".
- Provide inputs: product, platform, version, title.
- Download the "cover-image" artifact from the workflow run.

Output files are saved under `tools/public-release-post-cover/output/`.

## Deploy to QA (blog-qa.groupdocs.com)

- Run the workflow "Deploy to blog-qa.groupdocs.com".
- Requires repo secret `REPO_PAT` and AWS creds `ACCESS_KEY`/`SECRET_ACCESS`.
- Builds with `config.yml,config.staging.yml` and deploys to the `staging` target.

## Deploy to Production (blog.groupdocs.com)

- Run the workflow "Deploy to blog.groupdocs.com".
- Requires repo secret `REPO_PAT` and AWS creds `ACCESS_KEY`/`SECRET_ACCESS`.
- Builds with `config.yml,config.production.yml` and deploys to the `production` target.

## Translation status

⚠️ **1 post(s) missing translations**

### Summary

- **Total posts scanned**: 90
- **Posts with complete translations**: 89
- **Posts missing translations**: 1
- **Expected languages**: 21
- **Last updated**: 2026-01-24 06:15:35 UTC

### Posts Needing Attention

- [2026-01-20-compare-excel-spreadsheets-advanced-cell-by-cell-analysis-csharp](https://blog.groupdocs.com/comparison/compare-excel-spreadsheets-advanced-cell-by-cell-analysis-csharp/) - 21/21 translations missing
