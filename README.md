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

⚠️ **2 post(s) missing translations**

### Summary

- **Total posts scanned**: 128
- **Posts with complete translations**: 126
- **Posts missing translations**: 2
- **Expected languages**: 21
- **Last updated**: 2026-05-07 08:09:17 UTC

### Posts Needing Attention

- [2026-05-06-groupdocs-metadata-for-net-26-5](https://blog.groupdocs.com/metadata/groupdocs-metadata-for-net-26-5/) - 21/21 translations missing
- [2026-05-05-compare-pdf-documents](https://blog.groupdocs.com/comparison/compare-pdf-documents/) - 21/21 translations missing
