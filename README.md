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

- **Total posts scanned**: 176
- **Posts with complete translations**: 172
- **Posts missing translations**: 4
- **Expected languages**: 21
- **Last updated**: 2026-08-18 06:19:54 UTC

### Posts Needing Attention

- [2026-08-17-groupdocs-total-for-node-js-26-8](https://blog.groupdocs.com/total/groupdocs-total-for-node-js-26-8/) - 21/21 translations missing
- 2026-08-11-xmp-metadata-in-adobe-psd-and-ai-net - 21/21 translations missing
- 2026-08-11-xmp-metadata-in-adobe-psd-and-ai-java - 21/21 translations missing
- 2026-08-10-xmp-metadata-in-adobe-psd-and-ai-python - 21/21 translations missing
