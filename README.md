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

- **Total posts scanned**: 80
- **Posts with complete translations**: 77
- **Posts missing translations**: 3
- **Expected languages**: 21
- **Last updated**: 2025-12-26 06:16:00 UTC

### Posts Needing Attention

- [2025-12-25-groupdocs-viewer-for-java-25-12](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-java-25-12/) - 21/21 translations missing
- [2025-12-25-groupdocs-parser-for-net-25-12-1](https://blog.groupdocs.com/parser/groupdocs-parser-for-net-25-12-1/) - 21/21 translations missing
- [2025-12-25-groupdocs-comparison-for-python-25-12](https://blog.groupdocs.com/comparison/groupdocs-comparison-for-python-25-12/) - 21/21 translations missing
