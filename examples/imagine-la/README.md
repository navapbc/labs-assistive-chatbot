# ImagineLA Social Benefit Navigator

This is the original production implementation of the RAG chatbot, built for [ImagineLA](https://www.imaginela.org/) to help case managers in Los Angeles navigate public benefits and tax credits for their clients.

## What's Here

### engines.py

Three classes extracted from the core `chat_engine.py`:

- **`ImagineLaEngine`** — The main engine with extensive system prompts covering LA-specific benefit programs, canned responses for common questions, policy update alerts, and referral links to government resources.
- **`CaEddWebEngine`** — A simpler engine focused on California's Employment Development Department.
- **`ImagineLA_MessageAttributes`** — Extended message attributes adding `benefit_program`, `canned_response`, and `alert_message` fields.

### ingestion/

- **`imagine_la/`** — Contentful CMS scraper and HTML-to-chunks ingestion pipeline for the Benefits Information Hub content.
- **`la_policy/`** — Playwright-based scraper for LA County DPSS policy documents (dynamic JavaScript-rendered content).

### spiders/

Seven Scrapy spiders for California-specific data sources:

| Spider | Source | Dataset |
|--------|--------|---------|
| `edd_spider.py` | CA Employment Development Department | CA EDD |
| `ca_ftb_spider.py` | CA Franchise Tax Board | CA FTB |
| `ca_wic_spider.py` | WIC program | WIC |
| `covered_ca_spider.py` | Covered California | Covered California |
| `ca_public_charge_spider.py` | Keep Your Benefits | Keep Your Benefits |
| `irs_spider.py` | IRS tax credits | IRS |
| `la_policy_spider.py` | LA County DPSS Policy | DPSS Policy |

### refresh-ingestion.sh

Orchestration script that runs all scrapers and ingestion pipelines in sequence to refresh the full dataset.

## How to Reuse This

1. **Copy `engines.py`** to `app/src/engines/imagine_la_engine.py`
2. **Adjust imports:**
   ```python
   from src.chat_engine import BaseEngine, OnMessageResult, PROMPT
   from src.generate import MessageAttributes, analyze_message, ChatHistory
   ```
3. **Register in `app/src/engines/__init__.py`:**
   ```python
   import src.engines.imagine_la_engine  # noqa: F401
   ```
4. **Copy spiders** to `app/src/ingestion/scrapy_dst/spiders/`
5. **Copy ingestion scripts** to `app/src/ingestion/`
6. **Set up data sources** — You'll need Contentful API credentials for the Benefits Information Hub content, and a running PostgreSQL database with pgvector.
