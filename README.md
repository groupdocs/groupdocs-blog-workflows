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

⚠️ **17 post(s) missing translations**

### Summary

- **Total posts scanned**: 65
- **Posts with complete translations**: 48
- **Posts missing translations**: 17
- **Expected languages**: 21
- **Last updated**: 2025-12-09 06:15:56 UTC

### Posts Needing Attention

- [2025-11-11-groupdocs-watermark-for-net-25-11](https://blog.groupdocs.com/watermark/groupdocs-watermark-for-net-25-11/) - 21/21 translations missing
- [2025-11-11-groupdocs-watermark-for-net-25-10](https://blog.groupdocs.com/watermark/groupdocs-watermark-for-net-25-10/) - 21/21 translations missing
- [2025-11-17-groupdocs-viewer-for-net-ui-8-1-2](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-ui-8-1-2/) - 21/21 translations missing
- [2025-10-15-working-with-spreadsheets](https://blog.groupdocs.com/viewer/working-with-spreadsheets/) - 21/21 translations missing
- [2025-09-30-viewer-for-net-25-9](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-25-9/) - 21/21 translations missing
- [2025-09-29-viewer-for-java-25-9](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-java-25-9/) - 21/21 translations missing
- [2025-09-22-viewer-for-net-ui-8-1-1](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-ui-8-1-1/) - 21/21 translations missing
- [2025-09-02-viewer-for-net-25-8](https://blog.groupdocs.com/viewer/groupdocs-viewer-for-net-25-8/) - 21/21 translations missing
- [2025-07-15-working-with-fonts](https://blog.groupdocs.com/viewer/working-with-fonts/) - 21/21 translations missing
- [2025-11-11-groupdocs-total-for-net-25-9](https://blog.groupdocs.com/total/groupdocs-total-for-net-25-9/) - 21/21 translations missing
- [2025-11-02-groupdocs-total-for-java-25-10](https://blog.groupdocs.com/total/groupdocs-total-for-java-25-10/) - 21/21 translations missing
- [2025-10-27-groupdocs-total-for-python-25-10](https://blog.groupdocs.com/total/groupdocs-total-for-python-25-10/) - 21/21 translations missing
- [2025-10-07-groupdocs-total-for-net-25-9](https://blog.groupdocs.com/total/groupdocs-total-for-net-25-9/) - 21/21 translations missing
- [2025-10-01-groupdocs-total-for-net-25-8](https://blog.groupdocs.com/total/groupdocs-total-for-net-25-8/) - 21/21 translations missing
- [2025-08-20-groupdocs-total-for-net-25-7](https://blog.groupdocs.com/total/groupdocs-total-for-net-25-7/) - 21/21 translations missing
- [2025-10-01-blog-sign-documents-with-pkcs11-dotnet](https://blog.groupdocs.com/signature/sign-documents-with-pkcs11-dotnet/) - 21/21 translations missing
- [2025-11-17-groupdocs-search-for-net-25-11](https://blog.groupdocs.com/search/groupdocs-search-for-net-25-11/) - 21/21 translations missing
