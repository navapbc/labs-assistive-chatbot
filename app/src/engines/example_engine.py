"""
Example chat engine — a minimal template for building your own engine.

This engine inherits all RAG behavior from BaseEngine:
  1. Analyzes the user's message (system_prompt_1)
  2. Retrieves relevant document chunks via vector search
  3. Generates a response with citations (system_prompt_2)

To create your own engine:
  1. Copy this file and rename it (e.g., my_org_engine.py)
  2. Change engine_id, name, and datasets to match your data
  3. Customize system_prompt_2 for your domain
  4. Import the new module in src/engines/__init__.py
"""

from src.chat_engine import BaseEngine


class ExampleEngine(BaseEngine):
    # Unique identifier used in API URLs and configuration.
    engine_id: str = "example"

    # Human-readable name shown in the UI.
    name: str = "Example Chat Engine"

    # List of dataset labels to search when retrieving context.
    # These must match the dataset_label used during ingestion.
    # Example: datasets = ["My Knowledge Base", "FAQ Documents"]
    datasets: list[str] = []

    # Number of chunks to retrieve from the vector store.
    retrieval_k: int = 8

    # Minimum similarity score for retrieved chunks (-1 to disable filtering).
    retrieval_k_min_score: float = 0.45

    # Override system_prompt_2 to customize how the LLM responds.
    # The default prompt (inherited from BaseEngine) instructs the LLM to:
    #   - Use plain language and bullet points
    #   - Include citation numbers referencing retrieved context
    #   - Respond in the user's language
