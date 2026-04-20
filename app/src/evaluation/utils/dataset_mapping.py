"""Utility functions for dataset name mapping.

``DATASET_MAPPING`` lets users alias short CLI dataset IDs (e.g. ``"my_docs"``) to the
human-readable ``dataset_label`` values used in the DB (e.g. ``"My Docs"``).

It is intentionally empty in the template — extend it for your own deployment if you
want short CLI aliases for the evaluation commands.
"""

from types import MappingProxyType
from typing import Mapping

DATASET_MAPPING: Mapping[str, str] = MappingProxyType({})


def get_dataset_mapping() -> Mapping[str, str]:
    """Get mapping from CLI dataset names to DB dataset names."""
    return DATASET_MAPPING


def map_dataset_name(dataset_name: str) -> str:
    """Map a CLI dataset name to its DB dataset name.

    Falls back to returning ``dataset_name`` unchanged if no alias is registered.
    """
    return DATASET_MAPPING.get(dataset_name.lower(), dataset_name)
