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

⚠️ **4 post(s) missing translations**

### Summary

- **Total posts scanned**: 173
- **Posts with complete translations**: 169
- **Posts missing translations**: 4
- **Expected languages**: 21
- **Last updated**: 2026-08-13 07:06:16 UTC

### Posts Needing Attention

- [2026-08-12-extract-annotations-from-pdf-documents](https://blog.groupdocs.com/parser/extract-annotations-from-pdf-documents-net/) - 21/21 translations missing
- 2026-08-11-xmp-metadata-in-adobe-psd-and-ai-net - 21/21 translations missing
- 2026-08-11-xmp-metadata-in-adobe-psd-and-ai-java - 21/21 translations missing
- [2026-08-08-compare-metadata-between-document-versions-python](https://blog.groupdocs.com/metadata/compare-metadata-between-document-versions-python-net/) - 21/21 translations missing
