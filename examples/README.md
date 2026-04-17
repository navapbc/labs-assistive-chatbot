# Examples

This directory contains reference implementations showing how to configure the chatbot framework for a specific use case. Each example is a template to copy and adapt — not an importable package.

## Available Examples

### [california-edd/](california-edd/)

A chatbot over California's Employment Development Department (EDD) website. Includes a Scrapy spider for crawling edd.ca.gov, ingestion configuration, and a chat engine scoped to EDD programs (UI, SDI, PFL).

## How to Use Examples

Examples are **templates to copy and adapt**, not importable packages. To use one:

1. Copy the relevant files into your `app/src/` directory
2. Adjust imports to match the project structure (e.g., `from src.chat_engine import BaseEngine`)
3. Register new engines in `app/src/engines/__init__.py`
4. Run ingestion for your data sources
5. Set your engine as the default via the `CHAT_ENGINE` environment variable
