# QA Generation Module

This module provides tools for generating high-quality question-answer pairs from documents using LLM models.

## Overview

The QA generation module provides:
1. Generation of QA pairs from documents or chunks
2. Configurable LLM models and parameters
3. Stratified sampling for targeted generation
4. Simple storage with metadata tracking

## Usage

### Command Line Interface

The evaluation CLI provides QA generation commands:

```bash
# Generate QA pairs from all documents
make generate-qa

# Generate from a specific dataset with a custom LLM
make generate-qa dataset="<your_dataset_id>" llm="gpt-4o-mini"

# Sample 10% of documents with a fixed seed
make generate-qa sampling=0.1 random_seed=42
```

Arguments:

- `dataset`: Optional. One or more dataset IDs, space-separated (e.g., `"<dataset_a> <dataset_b>"`). If omitted, all datasets registered in the codebase are used. The set of valid dataset IDs is determined by the ingestion scripts under `app/src/ingestion/`.
- `llm`: LLM model to use (default: `"gpt-4o-mini"`)
- `sampling`: Fraction of documents to sample (e.g., `0.1`)
- `random_seed`: Random seed for reproducible sampling
- `output_dir`: Base directory for storing results (default: `src/evaluation/data`)

## Data Storage

Generated QA pairs are stored in a simple directory structure:

```
src/evaluation/data/qa_pairs/
├── qa_pairs.csv        # Generated QA pairs
└── metadata.json       # Generation metadata
```

### QA Pairs CSV Format

The `qa_pairs.csv` file contains:
- `id`: Stable identifier for the QA pair
- `question`: Generated question text
- `answer`: Generated answer text
- `document_name`: Source document name
- `document_source`: Source system (e.g., `"<your_dataset_id>"`)
- `dataset`: Dataset identifier
- `document_id`: Source document ID
- `chunk_id`: Source chunk ID (if from chunks)
- `content_hash`: Hash of source content
- `created_at`: Generation timestamp
- `llm_model`: LLM model used

### Generation Metadata

The `metadata.json` file tracks:
```json
{
  "timestamp": "2024-02-20T12:34:56",
  "llm_model": "gpt-4o-mini",
  "total_pairs": 1000,
  "datasets": ["..."],
  "git_commit": "abc123",
  "generation_config": {
    "question_source": "chunk",
    "questions_per_unit": 1,
    "sample_fraction": 0.1
  }
}
```