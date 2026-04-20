# Nava Labs Assistive Chatbot

**An open-source generative AI chatbot that uses vetted sources of truth to answer benefits program questions, backed up by direct quote citations.**

Built by [Nava Labs](https://www.navapbc.com/labs/ai-tools-public-benefits), a division of [Nava PBC](https://www.navapbc.com).

**[About](#about)** · **[Features](#features)** · **[How it works](#how-it-works)** · **[Components](#components)** · **[Setup](#setup)** · **[Evaluation](#evaluation)** · **[Contributing](#contributing)** · **[License](#license)**

---

## About

Navigating and enrolling in benefits programs is challenging, with complex policies and application processes. Many people need help from support professionals like caseworkers, call-center specialists, and community outreach specialists. Yet because benefits programs are so complicated, even these staff can benefit from support to help them help others navigate and enroll in government programs.

The [Assistive Chatbot](https://www.navapbc.com/labs/caseworker-ai-tools/assistive-chatbot) is a  part of Nava Labs' broader [Caseworker Empowerment Toolkit](https://www.caseworker.navapbc.com).

**Initial development and piloting:**

The Assistive Chatbot was initially developed with funding from Gates Foundation, in partnership with [Amplifi](https://www.amplifi.org/). 125 staff members in public-facing roles across six direct service organizations tested the tool in a 3-month pilot period running March to June 2025. Our pilot evaluation showed the chatbot is estimated to improve caseworker accuracy by an average of 40% with stronger improvements for more difficult client questions. Nava Labs has published our in-depth pilot findings:
- [Evaluating a Gen-AI powered Assistive Chatbot for Caseworkers](https://www.navapbc.com/case-studies/evaluating-ai-assistive-chatbot-caseworkers)

**Who this is for:**

- **Caseworkers and benefit navigators** who help clients enroll in public benefit programs
- **Government agencies and social services organizations** developing AI tools for their workforce
- **Developers** looking to build or adapt AI-assisted casework tools for their context

---

## Features

- **Integrated in context** - A REST API makes the chatbot available for integration into the systems where caseworkers are already working
- **Vetted sources of truth** — Ingests domain-specific content (policy documents, knowledge-base articles, internal documentation, web-based content, etc.) and indexes it for semantic search
- **Direct quote citations with every answer** — Provides direct quote citations to back up LLM-generated responses
- **Summarize and translate in a conversational interface** — Includes inherent LLM capabilties like summarization and language translation to make complext benefits information easy to understand
- **Sticks to what it knows** - Built-in guardrails prevent the chatbot from answering out-of-scope questions that aren't covered by its designated sources
- **Flexible AI model support** — works with multiple LLM providers

---

## How it works

The chatbot follows a standard RAG pipeline: source content is ingested and indexed into a vector database, then user questions are answered by retrieving relevant chunks and passing them to an LLM as context.

```mermaid
flowchart LR
    subgraph Ingestion
        A[Source documents<br/>web pages, PDFs, etc.] --> B[Scrapy / Playwright /<br/>Beautiful Soup]
        B --> C[Tree-based chunking<br/>ingester.py]
        C --> D[Embedding model]
        D --> E[(pgvector DB)]
    end

    subgraph Retrieval & Generation
        U([User]) --> F[Chat UI<br/>Chainlit]
        U --> G[REST API<br/>FastAPI]
        F --> H[Semantic search]
        G --> H
        E --> H
        H --> I[LiteLLM]
        I --> J[LLM provider<br/>OpenAI / Ollama / etc.]
        J --> K[Response<br/>with citations]
        K --> F
        K --> G
    end
```

## Components

This template is built on Nava's open-source [infrastructure template](https://github.com/navapbc/template-infra) and [Python application template](https://github.com/navapbc/template-application-flask/), part of [Nava's Platform](https://github.com/navapbc/platform).

- The application is hosted in AWS, with infrastructure defined via Terraform in [/infra](./infra).
- The application code is written in Python and lives in [/app/src](./app/src).
  - Chainlit and FastAPI provide the chat UI and a REST API for third-party integrations.
  - LiteLLM provides a vendor-agnostic interface for accessing LLMs.
- The application uses AWS Aurora Serverless v2 in deployed environments and Postgres locally. SQLAlchemy is used as the ORM, with Alembic and Pydantic managing the schema. Model definitions live in [app/src/db/models](./app/src/db/models).
  - The `pgvector` extension provides a `vector` type used for semantic search and document retrieval.
- Source documentation is scraped, parsed, and indexed via [ingest_runner.py](./app/src/ingest_runner.py), which uses Scrapy, Playwright, and Beautiful Soup. A custom "tree-based chunking" pipeline in [ingester.py](./app/src/ingester.py) splits content into semantically-meaningful chunks.
- Evaluation code for measuring retrieval-pipeline performance is in [/app/notebooks/metrics](./app/notebooks/metrics).
- Additional exploratory code and notebooks live in [/app/notebooks](./app/notebooks).

## Setup

To set up your local development environment, follow the instructions in [Getting Started](docs/app/getting-started.md).

See [Deployments and Releases](docs/releases.md) for information about deploying to your environments.

### Managing the chatbot's data

To learn more about how to configure data ingestion and refresh the indexed content, see [Data Management](docs/data-management.md).

## Evaluations

The chatbot includes built-in commands for research and evaluation, including batch processing and exporting user interaction logs. See [Special Commands](docs/special-commands.md).

You can also run [promptfoo](https://www.promptfoo.dev/) evaluations against multiple test inputs using Google Sheets. See [Promptfoo Evaluations](docs/app/evaluation/promptfoo-google-sheets.md).

## Contributing

We welcome contributions from the community — whether you're fixing a bug, suggesting a feature, or improving documentation.

Please read our [Contributing Guide](CONTRIBUTING.md) before submitting a pull request. All contributors are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

For security-related issues, please review our [Security Policy](SECURITY.md) before disclosing publicly.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE). You are free to use, modify, and distribute this software in accordance with the license terms.

---

## About Nava

[Nava PBC](https://www.navapbc.com) partners with government agencies to design and build simple, effective digital services. As a public benefit corporation, we're accountable to our mission: making it easier for people to access the services they need.

[Nava Labs](https://www.navapbc.com/labs) uses philanthropic funding to prototype safety-net innovations that government agencies need but can’t fund directly. We build and test new approaches to delivering public services, evaluate what works, and advocate for scaling proven solutions.
