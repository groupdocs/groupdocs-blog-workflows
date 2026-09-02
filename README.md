# GroupDocs Blog Workflows

GitHub Actions that build and deploy the GroupDocs blog.

Every workflow is manual (`workflow_dispatch`). Each one checks out
[`groupdocs/groupdocs-blog`](https://github.com/groupdocs/groupdocs-blog) — including
submodules — builds it with Hugo 0.101.0 (extended), and publishes the result. The site
content itself lives in that repo, not here.

All four require the `REPO_PAT` secret to check out the blog repo.

## Deploy to blog-qa.groupdocs.com (S3)

`deploy-qa.yml` — GitHub-hosted runner.

Builds with `config.yml,config.staging.yml` and `--buildDrafts`, deploys via
`hugo deploy` to the `staging` target, then invalidates CloudFront.

Secrets: `ACCESS_KEY`, `SECRET_ACCESS`, `CLOUDFRONT_DISTRIBUTION_ID_STAGING`

## Deploy to blog.groupdocs.com (S3)

`deploy-prod.yml` — GitHub-hosted runner.

Builds with `config.yml,config.production.yml` (no drafts), deploys via `hugo deploy` to
the `production` target, then invalidates CloudFront.

Secrets: `ACCESS_KEY`, `SECRET_ACCESS`, `CLOUDFRONT_DISTRIBUTION_ID`

## Deploy to blog-qa.groupdocs.com (Ceph)

`deploy-qa-ceph.yml` — self-hosted runner.

Builds the staging config with `--buildDrafts`, uploads `public/` to the
`blog-qa-groupdocs-com` Ceph bucket with the AWS CLI, then purges the Bunny.net cache.

Secrets: `CEPH_REGION`, `CEPH_QA_ACCESS_KEY_ID`, `CEPH_QA_SECRET_ACCESS_KEY`,
`CEPH_QA_ENDPOINT_URL`, `BUNNYNET_ACCESS_KEY`, `BUNNYNET_PURGE_URL`

## Deploy to blog.groupdocs.com (Ceph)

`deploy-prod-ceph.yml` — self-hosted runner.

Builds the production config, uploads `public/` to the `blog-groupdocs-com` Ceph bucket
with the AWS CLI, then purges the Bunny.net cache.

Secrets: `CEPH_REGION`, `CEPH_PROD_ACCESS_KEY_ID`, `CEPH_PROD_SECRET_ACCESS_KEY`,
`CEPH_PROD_ENDPOINT_URL`, `BUNNYNET_ACCESS_KEY`, `BUNNYNET_PURGE_URL`
