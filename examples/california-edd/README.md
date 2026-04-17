# California EDD Example

A reference implementation for building a chatbot over California's [Employment Development Department (EDD)](https://edd.ca.gov/) website.

## What's Here

### engines.py

`CaEddWebEngine` — A chat engine scoped to EDD programs (Unemployment Insurance, State Disability Insurance, Paid Family Leave). Restricts responses to EDD content only and prompts the user to clarify which EDD program they're asking about when ambiguous.

### spiders/edd_spider.py

A Scrapy spider that crawls `edd.ca.gov/en/` and extracts page content as structured JSON. Handles EDD-specific HTML patterns including accordion sections and tab panes. Scrapy discovers spiders under `scrapy_dst/spiders/` (per the `SPIDER_MODULES` setting), so the spider must be moved there before it can be run.

### ingestion/ingest_runner.py

Shows how `edd_config` configures ingestion for scraped EDD content (including EDD-specific markdown fixes applied before chunking). This repo's `app/src/ingest_runner.py` already contains this function and an `"edd"` case in `get_ingester_config()`; the file here is a reference for adapting the pattern to a different app.

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

This repo's `app/src/ingest_runner.py` already registers the `"edd"` dataset, so you can ingest the JSON directly:

```bash
cd app
poetry run ingest-runner edd --json_input /absolute/path/to/edd_scrapings.json
```

If you are adapting this example to a different app that does not already have `edd_config`, copy the function from `ingestion/ingest_runner.py` into your app's `ingest_runner.py` and add a case to `get_ingester_config()`:

```python
case "edd":
    return edd_config("CA EDD", "employment", "California", scraper_dataset)
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
