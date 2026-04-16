# Examples

This directory contains reference implementations that were extracted from the core chatbot framework. Each example shows how a real organization configured the framework for their specific use case.

## Available Examples

### [imagine-la/](imagine-la/)

The original ImagineLA Social Benefit Navigator implementation. This was a production chatbot used by case managers in the Los Angeles region to help clients navigate public benefits and tax credits.

Includes:
- **Engine classes** with custom system prompts, canned responses, and policy alert handling
- **Ingestion scripts** for Contentful CMS content and LA County policy documents
- **Web scrapers** (Scrapy spiders) for 7 California-specific data sources
- **Ingestion orchestration** script for refreshing all data sources

## How to Use Examples

Examples are **templates to copy and adapt**, not importable packages. To use one:

1. Copy the relevant files into your `app/src/` directory
2. Adjust imports to match the project structure (e.g., `from src.chat_engine import BaseEngine`)
3. Register new engines in `app/src/engines/__init__.py`
4. Run ingestion for your data sources
5. Update `app_config.py` to set your engine as the default
