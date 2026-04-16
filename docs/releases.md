# Deployments and releases

Deployed instances of the chatbot typically run in at least two environments, `dev` and `prod`. You can add additional environments as needed — see [Runbook Cheat Sheet](runbook-cheat-sheet.md) for standing up a new instance.

`dev` is a CD environment; merges to `main` automatically trigger a deploy.

## Deploying to production

Prod deploys are triggered manually:

1. On the Releases page of your GitHub repo, select **Draft a new release**.
1. Under **Choose a tag**, create a new tag, bumping the version number per [semantic versioning](https://semver.org/).
1. Select **Generate release notes** to pre-populate the form. Adjust the notes as needed.
1. Click **Publish release**.
1. Navigate to the `Deploy App` GitHub Actions workflow (`.github/workflows/cd-app.yml`) in your repo.
1. Click **Run workflow**.
1. Under **Environment to deploy to**, select `prod`.
1. Under **Tag or branch or SHA to deploy**, enter the tag you just created (e.g., `v1.4.0`).
1. Click **Run workflow** (leave **Use workflow from** at its default).

We follow [semantic versioning](https://semver.org/) for version numbers.

## Release management

Several Makefile targets automate cutting and deploying releases. In most cases the release process is driven by GitHub Actions and you won't run these directly, but they're available for test deploys from local changes.

### Build a release

```bash
make release-build APP_NAME=<APP_NAME>
```

This calls the `release-build` target in `<APP_NAME>/Makefile` with parameters to build an image. `<APP_NAME>/Dockerfile` should have a build stage named `release` acting as the build target (see [Docker's multi-stage build docs](https://docs.docker.com/build/building/multi-stage/#name-your-build-stages)).

You can pass `IMAGE_NAME` and `IMAGE_TAG` to override those aspects of the built image; typically leave them at the defaults, which are based on `APP_NAME` and the latest commit hash.

### Publish a release

```bash
make release-publish APP_NAME=<APP_NAME>
```

### Deploy a release

```bash
make release-deploy APP_NAME=<APP_NAME> ENVIRONMENT=<ENV>
```

### All together

For a test deploy of local changes, chain the targets:

```bash
make release-build release-publish release-deploy APP_NAME=<APP_NAME> ENVIRONMENT=<ENV>
```

You may also need `release-run-database-migrations` before `release-deploy` — be careful, as this will apply migrations against the target environment.
