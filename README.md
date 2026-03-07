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

⚠️ **3 post(s) missing translations**

### Summary

- **Total posts scanned**: 99
- **Posts with complete translations**: 96
- **Posts missing translations**: 3
- **Expected languages**: 21
- **Last updated**: 2026-03-07 06:23:50 UTC

### Posts Needing Attention

- [2026-03-05-groupdocs-signature-for-net-26-2](https://blog.groupdocs.com/signature/groupdocs-signature-for-net-26-2/) - 21/21 translations missing
- [2026-03-05-parsing-archives-to-extract-text](https://blog.groupdocs.com/parser/extract-text-from-zip-rar-archives/) - 21/21 translations missing
- [2026-03-06-compare-word-documents](https://blog.groupdocs.com/comparison/compare-word-documents/) - 21/21 translations missing
