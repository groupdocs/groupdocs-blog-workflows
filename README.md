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

- **Total posts scanned**: 91
- **Posts with complete translations**: 90
- **Posts missing translations**: 1
- **Expected languages**: 21
- **Last updated**: 2026-01-28 06:19:31 UTC

### Posts Needing Attention

- [2026-01-27-groupdocs-total-for-net-25-12](https://blog.groupdocs.com/total/groupdocs-total-for-net-25-12/) - 21/21 translations missing
