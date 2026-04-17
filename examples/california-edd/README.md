# California EDD Example

A reference implementation for building a chatbot over California's [Employment Development Department (EDD)](https://edd.ca.gov/) website.

## What's Here

### engines.py

`CaEddWebEngine` — A chat engine scoped to EDD programs (Unemployment Insurance, State Disability Insurance, Paid Family Leave). Restricts responses to EDD content only and prompts the user to clarify which EDD program they're asking about when ambiguous.

### spiders/edd_spider.py

A Scrapy spider that crawls `edd.ca.gov/en/` and extracts page content as structured JSON. Handles EDD-specific HTML patterns including accordion sections and tab panes.

> **Note:** This file lives in `spiders/` for reference purposes as part of the examples directory. In the main application, it belongs at `app/src/ingestion/scrapy_dst/spiders/edd_spider.py` so that Scrapy's `SPIDER_MODULES = ["scrapy_dst.spiders"]` setting can discover it automatically.

### ingestion/ingest_runner.py

The `edd_config` function configures how scraped EDD content is processed and ingested into the vector store. Shows how to fix EDD-specific markdown quirks before chunking.

### scrapy_runner.py / scrapy.cfg / scrapy_dst/

Scrapy project infrastructure. `scrapy_runner.py` is the entry point for running spiders. The `scrapy_dst/spiders/` directory is where Scrapy discovers spiders at runtime — any spider you want to run must be placed there.

## How to Use

### 1. Set up the spider

Copy the spider into the Scrapy project's spider discovery directory:

```bash
cp spiders/edd_spider.py app/src/ingestion/scrapy_dst/spiders/edd_spider.py
```

Then run it to collect EDD content:
```bash
cd app/src/ingestion
python scrapy_runner.py edd
```

This produces `edd_scrapings.json`.

### 2. Ingest the content

Copy the `edd_config` function from `ingestion/ingest_runner.py` into `app/src/ingest_runner.py` and add an `"edd"` case to `get_ingester_config()`:

```python
case "edd":
    return edd_config("CA EDD", "employment", "California", scraper_dataset)
```

Then run ingestion:
```bash
poetry run ingest-runner edd --json_input path/to/edd_scrapings.json
```

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
