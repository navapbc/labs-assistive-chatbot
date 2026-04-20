# Managing data

## Data ingestion overview

Chat engines (defined in [app/src/chat_engine.py](../app/src/chat_engine.py) and subclassed under [app/src/engines/](../app/src/engines/)) are downstream consumers of data sources. To add a new engine, create a class with the following attributes:

- `engine_id` — determines the endpoint the chatbot will serve this engine from
- `name` — human-readable name
- `datasets` — list of dataset labels the engine will search against (each must match a `dataset_label` used during ingestion)
- `formatting_config` — determines how the chat engine's response is formatted

## Loading documents

The application supports ingesting data from multiple source types, including web scraping (Scrapy/Playwright), JSON inputs, and PDFs. Each dataset is ingested with [ingest_runner.py](../app/src/ingest_runner.py), configured via CLI flags for simple cases or a `--config-module` for custom preprocessing.

### Configuring a new dataset

For most data sources, no code changes are required — pass the dataset configuration directly as CLI flags:

```bash
cd app
poetry run ingest-runner <dataset_id> \
  --dataset-label="My Docs" \
  --benefit-program=general \
  --benefit-region=global \
  --common-base-url=https://example.com/ \
  --json_input=path/to/scrapings.json
```

Then reference the `dataset_label` from a chat engine's `datasets` list.

The default behavior expects each JSON item to contain:

- `url` — document source URL
- `title` — document title
- `markdown` *(preferred)*, or `main_content` / `main_primary` — document body in Markdown

If your source uses different field names or needs custom pre-processing, write a Python module exposing a `build_config(...)` function and pass it via `--config-module`. See [examples/california-edd/ingestion/edd_config.py](../examples/california-edd/ingestion/edd_config.py) for a worked example.

### Running ingestion

Ingest a single dataset from a JSON file:

```bash
poetry run ingest-runner my_dataset \
  --dataset-label="My Docs" \
  --common-base-url=https://example.com/ \
  --json_input=/path/to/scrapings.json
```

For datasets that need credentials (API tokens, etc.), set them in `.env` first. Do not hardcode secrets.

### Resuming ingestion for large datasets

Use `--resume` to continue from where a previous run stopped (commits per-document rather than at the end):

```bash
poetry run ingest-runner my_dataset --json_input=/path/to/scrapings.json --resume
```

### Dropping a dataset before re-ingesting

```bash
poetry run ingest-runner my_dataset --dataset-label="My Docs" --drop-only
```

### Skipping DB access

For dry runs or exporting markdown files only, use `--skip_db`:

```bash
poetry run ingest-runner my_dataset --json_input=/path/to/scrapings.json --skip_db
```

### Web scraping

For Scrapy-based datasets, run your spider to produce the JSON that the ingester consumes:

```bash
make scrapy-runner args="<spider_name> --debug"
```

For datasets that need dynamic-content scraping (e.g. via Playwright), wire a dedicated scraper up in your example or deployment. [examples/california-edd/](../examples/california-edd/) shows one end-to-end pattern.

### Loading documents in a deployed environment

The deployed application includes an S3 bucket following the pattern `s3://<app-name>-<env>` (e.g. `s3://my-chatbot-dev`). After authenticating with AWS, upload the JSON and invoke the runner in ECS:

```bash
aws s3 cp path/to/scrapings.json s3://<app-name>-<ENVIRONMENT>/
./bin/run-command app <ENVIRONMENT> '["ingest-runner", "<dataset_id>", "--dataset-label", "My Docs", "--common-base-url", "https://example.com/", "--json_input", "s3://<app-name>-<ENVIRONMENT>/scrapings.json"]'
```

Add `"--resume"` for large datasets.

## Backing up DB contents

When re-ingesting, new UUIDs are generated for chunks and documents, which can make diagnosing problems harder when logs refer to UUIDs that no longer exist. Before re-ingesting, create a backup so you can reference old UUIDs by restoring the backup to a local DB.

To back up DB contents for the `dev` deployment:

```sh
TARGET_ENV=dev
./bin/terraform-init infra/app/service $TARGET_ENV
./bin/run-command app $TARGET_ENV '["poetry", "run", "pg-dump", "backup"]'
aws s3 ls "s3://<app-name>-$TARGET_ENV/pg_dumps/"
```

For `prod`, replace `dev` with `prod` and re-run `./bin/terraform-init` first. Verify the new dump appears in the S3 `pg_dumps/` folder.

### Restoring DB contents locally

```bash
make pg-dump args="restore --dumpfile db.dump"
```

Replace `db.dump` with the file downloaded from S3. Run `make pg-dump args="--help"` for more options.
