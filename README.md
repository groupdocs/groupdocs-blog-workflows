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

⚠️ **11 post(s) missing translations**

### Summary

- **Total posts scanned**: 69
- **Posts with complete translations**: 58
- **Posts missing translations**: 11
- **Expected languages**: 21
- **Last updated**: 2025-12-12 06:16:07 UTC

### Posts Needing Attention

- [2025-11-11-groupdocs-watermark-for-net-25-11](https://blog.groupdocs.com/watermark/groupdocs-watermark-for-net-25-11/) - 21/21 translations missing
- [2025-11-11-groupdocs-watermark-for-net-25-10](https://blog.groupdocs.com/watermark/groupdocs-watermark-for-net-25-10/) - 21/21 translations missing
- [2025-12-09-groupdocs-viewer-for-net-25-11](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-25-11/) - 21/21 translations missing
- [2025-11-17-groupdocs-viewer-for-net-ui-8-1-2](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-ui-8-1-2/) - 21/21 translations missing
- [2025-10-15-working-with-spreadsheets](https://blog.groupdocs.com/viewer/working-with-spreadsheets/) - 21/21 translations missing
- [2025-09-30-viewer-for-net-25-9](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-25-9/) - 21/21 translations missing
- [2025-09-29-viewer-for-java-25-9](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-java-25-9/) - 21/21 translations missing
- [2025-09-22-viewer-for-net-ui-8-1-1](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-ui-8-1-1/) - 21/21 translations missing
- [2025-09-02-viewer-for-net-25-8](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-25-8/) - 21/21 translations missing
- [2025-07-15-working-with-fonts](https://blog.groupdocs.com/viewer/working-with-fonts/) - 21/21 translations missing
- [2025-12-11-groupdocs-assembly-for-net-25-12](https://blog.groupdocs.com/assembly/groupdocs-assembly-for-net-25-12/) - 21/21 translations missing
