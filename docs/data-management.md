# Managing data

## Data ingestion overview

Chat engines (defined in [app/src/chat_engine.py](../app/src/chat_engine.py)) are downstream consumers of data sources. To add a new engine, create a class with the following attributes:

- `engine_id` — determines the endpoint the chatbot will serve this engine from
- `name` — human-readable name
- `datasets` — list of dataset IDs the engine will draw from (each must match the name of an ingestion dataset's script, see below)
- `formatting_config` — determines how the chat engine's response is formatted

## Loading documents

The application supports ingesting data from multiple source types, including web scraping (Scrapy/Playwright), JSON inputs, and PDFs. Each dataset is defined by an ingestion script under `app/src/ingestion/` and is addressed by a `dataset_id`.

The `./refresh-ingestion.sh` script orchestrates scraping and ingestion for any registered dataset. The sections below first describe how to use this script, then detail each underlying step in case you want to run them individually.

### Configuring a new dataset

To add a new data source:

1. Add an ingestion script under `app/src/ingestion/<your_dataset_id>/` following the pattern used by existing datasets in that directory.
2. Register the dataset ID so it can be invoked via `make scrapy-runner` and `make ingest-runner`.
3. Reference the dataset from a chat engine's `datasets` list.

If your data source requires credentials (API tokens, space IDs, etc.), add those as environment variables in your local `.env` and document them alongside your dataset script. Do not hardcode secrets.

### Refreshing all data sources

Before refreshing, create a backup of the database — see [Backing up DB contents](#backing-up-db-contents) below.

From within `/app`, run:

```bash
./refresh-ingestion.sh all
```

The `refresh-ingestion.sh` script only modifies the local database. To update the database in the deployed environments, the script generates two helper scripts in the top-level directory: `refresh-dev-*.sh` and `refresh-prod-*.sh`. Review these before running — they start ingestion of each dataset in parallel.

About 10 minutes after running `refresh-dev-*.sh`, you can check status and wait for completion:

```bash
cd app
DEPLOY_ENV=dev ./refresh-ingestion.sh wait_until_done
```

### Refreshing a specific data source

```bash
./refresh-ingestion.sh <your_dataset_id>
```

If the dataset requires credentials, export them first (or set them in `.env`):

```bash
export MY_DATASET_API_TOKEN="..."
./refresh-ingestion.sh <your_dataset_id>
```

### Manual process: individual steps

The following sections describe each step performed by `refresh-ingestion.sh` in case you want to run them independently.

### Web scraping

For manual scraping of a Scrapy-based dataset:

```bash
make scrapy-runner args="<your_dataset_id> --debug"
```

For datasets that require dynamic-content scraping (e.g., via Playwright), add a dedicated make target in the `Makefile` that runs the appropriate scraper before invoking `scrapy-runner`.

### Loading documents locally

For manual ingestion, use `make ingest-runner` with the dataset ID and the path to your scraped JSON:

```bash
make ingest-runner args="<your_dataset_id> --json_input=src/ingestion/<your_dataset_id>/scrapings.json"
```

For datasets that ingest from a directory of files rather than JSON, define a dedicated make target (e.g., `ingest-<your_dataset_id>`) that passes the required parameters:

```bash
make ingest-<your_dataset_id> DATASET_ID="My Dataset" FILEPATH=src/ingestion/<your_dataset_id>/pages
```

Notes on parameters:

- `DATASET_ID` is used in the chat UI to prefix each citation — use a user-friendly identifier (e.g., "Product Docs" or "HR Policies").
- The same `DATASET_ID` can be used for multiple documents to indicate they belong to the same dataset.
- Any additional metadata fields your ingestion script accepts (categories, regions, tags, etc.) should be documented in the dataset's own README.

The Docker container mounts the `/app` folder, so `FILEPATH` should be relative to `/app`. `/app/documents` is ignored by git — a good place for files you want to load but not commit.

### Loading documents in a deployed environment

The `refresh-ingestion.sh` script generates deployment scripts for both dev and prod environments (`refresh-dev-YYYY-MM-DD.sh` and `refresh-prod-YYYY-MM-DD.sh` in the top-level directory).

For manual deployment, the deployed application includes an S3 bucket following the pattern `s3://<app-name>-<env>` (e.g., `s3://my-chatbot-dev`). After authenticating with AWS, from the root of the repo run:

```bash
aws s3 cp path/to/scrapings.json s3://<app-name>-<ENVIRONMENT>/
./bin/run-command app <ENVIRONMENT> '["ingest-runner", "<your_dataset_id>", "--json_input", "s3://<app-name>-<ENVIRONMENT>/scrapings.json"]'
```

#### Resuming ingestion for large datasets

For large datasets, use the `--resume` flag to continue ingestion from where it last stopped:

```bash
./bin/run-command app <ENVIRONMENT> '["ingest-runner", "<your_dataset_id>", "--json_input", "s3://<app-name>-<ENVIRONMENT>/scrapings.json", "--resume"]'
```

This commits the DB transaction per `Document` instead of committing after all records are added.

### Skipping DB access

For dry runs or for exporting markdown files, skip reading and writing to the DB during ingestion with `--skip_db`:

```bash
make ingest-runner args="<your_dataset_id> --json_input=path/to/scrapings.json --skip_db"
```

Or set the environment variable before running `refresh-ingestion.sh`:

```bash
export SKIP_LOCAL_EMBEDDING=true
./refresh-ingestion.sh <your_dataset_id>
```

## Backing up DB contents

When reingesting, new UUIDs are generated for chunks and documents, which can make diagnosing problems harder when logs refer to UUIDs that no longer exist. Before running `refresh-ingestion.sh`, create a backup so you can reference old UUIDs by restoring the backup to a local DB.

To back up DB contents for the `dev` deployment:

```sh
TARGET_ENV=dev
./bin/terraform-init infra/app/service $TARGET_ENV
./bin/run-command app $TARGET_ENV '["poetry", "run", "pg-dump", "backup"]'
aws s3 ls "s3://<app-name>-$TARGET_ENV/pg_dumps/"
```

For `prod`, replace `dev` with `prod` and re-run `./bin/terraform-init` first. Verify the new dump appears in the S3 `pg_dumps/` folder.

### Restoring DB contents locally

To restore DB contents locally:

```bash
make pg-dump args="restore --dumpfile db.dump"
```

Replace `db.dump` with the file downloaded from S3. Run `make pg-dump args="--help"` for more options.
