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

⚠️ **6 post(s) missing translations**

### Summary

- **Total posts scanned**: 179
- **Posts with complete translations**: 173
- **Posts missing translations**: 6
- **Expected languages**: 21
- **Last updated**: 2026-08-23 06:18:42 UTC

### Posts Needing Attention

- [2026-08-21-remove-pii-from-office-files-nodejs](https://blog.groupdocs.com/metadata/remove-pii-from-office-files-nodejs-java/) - 21/21 translations missing
- [2026-08-21-remove-pii-from-office-files-net](https://blog.groupdocs.com/metadata/remove-pii-from-office-files-net/) - 21/21 translations missing
- [2026-08-21-remove-pii-from-office-files-java](https://blog.groupdocs.com/metadata/remove-pii-from-office-files-java/) - 21/21 translations missing
- 2026-08-11-xmp-metadata-in-adobe-psd-and-ai-net - 21/21 translations missing
- 2026-08-11-xmp-metadata-in-adobe-psd-and-ai-java - 21/21 translations missing
- 2026-08-10-xmp-metadata-in-adobe-psd-and-ai-python - 21/21 translations missing
