# GroupDocs Blog Workflows

GitHub Actions and tools that support GroupDocs blog publishing.

## Create release cover image

- Run the Actions workflow "Create release post cover image".
- Provide inputs: product, platform, version, title.
- Download the "cover-image" artifact from the workflow run.

Output files are saved under `tools/public-release-post-cover/output/`.

## Deploy to QA (blog-qa.groupdocs.com)

- Run the workflow "Deploy to blog-qa.groupdocs.com".
- Requires repo secret `REPO_TOKEN` and AWS creds `ACCESS_KEY`/`SECRET_ACCESS`.
- Builds with `config.yml,config.staging.yml` and deploys to the `staging` target.

## Deploy to Production (blog.groupdocs.com)

- Run the workflow "Deploy to blog.groupdocs.com".
- Requires repo secret `REPO_TOKEN` and AWS creds `ACCESS_KEY`/`SECRET_ACCESS`.
- Builds with `config.yml,config.production.yml` and deploys to the `production` target.

## Translation status

⚠️ **41 post(s) missing translations**

### Summary

- **Total posts scanned**: 65
- **Posts with complete translations**: 24
- **Posts missing translations**: 41
- **Expected languages**: 21
- **Last updated**: 2025-12-01 18:25:35 UTC

### Posts Needing Attention

- [2025-10-28-pythonnet-integration](https://blog.groupdocs.com/annotation/python-integration/) - 21/21 translations missing
- [2025-11-06-groupdocs-annotation-for-net-25-11](https://blog.groupdocs.com/annotation/groupdocs-annotation-for-net-25-11/) - 21/21 translations missing
- [2025-09-01-groupdocs-comparison-for-net-25-8](https://blog.groupdocs.com/comparison/groupdocs-comparison-for-net-25-8/) - 21/21 translations missing
- [2025-09-26-groupdocs-comparison-for-net-25-9](https://blog.groupdocs.com/comparison/groupdocs-comparison-for-net-25-9/) - 21/21 translations missing
- [2025-11-07-groupdocs-comparison-for-net-25-10](https://blog.groupdocs.com/comparison/groupdocs-comparison-for-net-25-10/) - 21/21 translations missing
- [2025-11-20-groupdocs-comparison-for-node-js-25-11](https://blog.groupdocs.com/comparison/groupdocs-comparison-for-node-js-25-11/) - 21/21 translations missing
- [2025-11-28-groupdocs-comparison-for-net-25-11](https://blog.groupdocs.com/comparison/groupdocs-comparison-for-net-25-11/) - 21/21 translations missing
- [2025-08-31-groupdocs-conversion-for-net-25-8](https://blog.groupdocs.com/conversion/groupdocs-conversion-for-net-25-8/) - 21/21 translations missing
- [2025-09-30-groupdocs-conversion-for-net-25-9](https://blog.groupdocs.com/conversion/groupdocs-conversion-for-net-25-9/) - 21/21 translations missing
- [2025-11-07-groupdocs-conversion-for-net-25-10](https://blog.groupdocs.com/conversion/groupdocs-conversion-for-net-25-10/) - 21/21 translations missing
