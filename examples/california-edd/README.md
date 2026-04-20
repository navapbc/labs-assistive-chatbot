# California EDD Example

A reference implementation for building a chatbot over California's [Employment Development Department (EDD)](https://edd.ca.gov/) website.

## What's Here

### engines.py

`CaEddWebEngine` — A chat engine scoped to EDD programs (Unemployment Insurance, State Disability Insurance, Paid Family Leave). Restricts responses to EDD content only and prompts the user to clarify which EDD program they're asking about when ambiguous.

### spiders/edd_spider.py

A Scrapy spider that crawls `edd.ca.gov/en/` and extracts page content as structured JSON. Handles EDD-specific HTML patterns including accordion sections and tab panes. Scrapy discovers spiders under `scrapy_dst/spiders/` (per the `SPIDER_MODULES` setting), so the spider must be moved there before it can be run.

### ingestion/edd_config.py

An EDD-specific ingestion config (custom `prep_json_item` plus markdown fix-ups for quirks in EDD pages). The generic `app/src/ingest_runner.py` loads this via the `--config-module` flag — no code changes to the core app are required.

### scrapy_runner.py / scrapy.cfg / scrapy_dst/

A self-contained Scrapy project. `scrapy_runner.py` is the entry point. `scrapy_dst/` holds settings, pipelines, and the `spiders/` discovery directory.

## How to Use

The example is a standalone Scrapy project — you can run the scrape in-place from `examples/california-edd/` without copying files into the app.

### 1. Scrape EDD content

Move the spider into Scrapy's discovery directory, then run it from this example directory:

```bash
cd examples/california-edd
mv spiders/edd_spider.py scrapy_dst/spiders/edd_spider.py
python scrapy_runner.py edd
```

This produces `edd_scrapings.json` in the current directory.

### 2. Ingest the content

Point the generic ingest runner at the EDD config module:

```bash
cd app
poetry run ingest-runner edd \
  --dataset-label="CA EDD" \
  --benefit-program=employment \
  --benefit-region=California \
  --common-base-url=https://edd.ca.gov/en/ \
  --config-module=examples.california_edd.ingestion.edd_config \
  --json_input=/absolute/path/to/edd_scrapings.json
```

If you are adapting this example to a different data source, write your own `build_config(...)` function (see `edd_config.py` for the signature) and pass it via `--config-module`. For straightforward sources, the runner's built-in defaults (maps `main_content`/`main_primary` → `markdown`) often suffice without any custom module.

### 3. Set up the engine

Copy `engines.py` to `app/src/engines/ca_edd_engine.py`.

Register it in `app/src/engines/__init__.py`:
```python
import src.engines.ca_edd_engine  # noqa: F401
```

Set it as the default in your environment:
```
CHAT_ENGINE=ca-edd-web
```
