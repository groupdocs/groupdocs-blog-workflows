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

⚠️ **29 post(s) missing translations**

### Summary

- **Total posts scanned**: 65
- **Posts with complete translations**: 36
- **Posts missing translations**: 29
- **Expected languages**: 21
- **Last updated**: 2025-12-05 06:15:31 UTC

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
- [2025-10-28-groupdocs-search-python-integration](https://blog.groupdocs.com/search/python-integration/) - 21/21 translations missing
- [2025-12-01-groupdocs-parser-for-net-25-11](https://blog.groupdocs.com/parser/groupdocs-parser-for-net-25-11/) - 21/21 translations missing
- [2025-11-13-groupdocs-parser-for-net-25-10](https://blog.groupdocs.com/parser/groupdocs-parser-for-net-25-10/) - 21/21 translations missing
- [2025-11-07-groupdocs-metadata-for-net-25-10](https://blog.groupdocs.com/metadata/groupdocs-metadata-for-net-25-10/) - 21/21 translations missing
- [2025-07-29-how-to-work-with-tags](https://blog.groupdocs.com/metadata/how-to-work-with-tag/) - 21/21 translations missing
- [2025-06-27-read-properties-in-gltf](https://blog.groupdocs.com/metadata/read-gltf/) - 21/21 translations missing
- [2025-06-06-edit-and-clean-xmp-in-svg](https://blog.groupdocs.com/metadata/edit-and-clean-xmp-in-svg/) - 21/21 translations missing
- [2025-11-28-groupdocs-merger-for-net-25-11](https://blog.groupdocs.com/merger/groupdocs-merger-for-net-25-11/) - 21/21 translations missing
- [2025-09-08-groupdocs-merger-for-net-25-9](https://blog.groupdocs.com/merger/groupdocs-merger-for-net-25-9/) - 21/21 translations missing
- [2025-09-12-groupdocs-markdown-first-public-release](https://blog.groupdocs.com/markdown/groupdocs-markdown-for-net-first-public-release/) - 21/21 translations missing
- [2025-09-01-groupdocs-markdown-for-net-announce](https://blog.groupdocs.com/markdown/groupdocs-markdown-for-net-announce/) - 21/21 translations missing
- [2025-11-13-groupdocs-editor-for-net-25-11](https://blog.groupdocs.com/editor/groupdocs-editor-for-net-25-11/) - 21/21 translations missing
