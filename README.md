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

- **Total posts scanned**: 161
- **Posts with complete translations**: 158
- **Posts missing translations**: 3
- **Expected languages**: 21
- **Last updated**: 2026-07-26 08:01:51 UTC

### Posts Needing Attention

- [2026-07-25-compare-metadata-between-document-versions-nodejs](https://blog.groupdocs.com/metadata/compare-document-metadata-nodejs/) - 21/21 translations missing
- [2026-07-25-compare-metadata-between-document-versions-net](https://blog.groupdocs.com/metadata/compare-metadata-versions-net/) - 21/21 translations missing
- [2026-07-25-compare-metadata-between-document-versions](https://blog.groupdocs.com/metadata/compare-metadata-versions-java/) - 21/21 translations missing
