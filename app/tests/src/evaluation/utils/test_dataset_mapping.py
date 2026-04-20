"""Tests for dataset name mapping utility."""

import pytest

from src.evaluation.utils import dataset_mapping as dataset_mapping_module
from src.evaluation.utils.dataset_mapping import (
    DATASET_MAPPING,
    get_dataset_mapping,
    map_dataset_name,
)


@pytest.fixture
def sample_mapping(monkeypatch):
    """Patch DATASET_MAPPING with a fixed sample so tests don't depend on real deployments."""
    from types import MappingProxyType

    sample = MappingProxyType({"foo": "Foo Dataset", "bar": "Bar Dataset"})
    monkeypatch.setattr(dataset_mapping_module, "DATASET_MAPPING", sample)
    return sample


def test_default_mapping_is_empty():
    """The template ships with an empty mapping; deployments extend it."""
    assert dict(DATASET_MAPPING) == {}


def test_get_dataset_mapping(sample_mapping):
    mapping = get_dataset_mapping()

    assert mapping["foo"] == "Foo Dataset"
    assert set(mapping.keys()) == {"foo", "bar"}
    assert mapping == sample_mapping

    # Returned mapping is immutable.
    with pytest.raises(TypeError):
        mapping["test"] = "TEST"  # type: ignore[index]
    with pytest.raises(TypeError):
        del mapping["foo"]  # type: ignore[attr-defined]


def test_map_dataset_name(sample_mapping):
    assert map_dataset_name("foo") == "Foo Dataset"
    assert map_dataset_name("bar") == "Bar Dataset"

    # Case insensitive.
    assert map_dataset_name("FOO") == "Foo Dataset"
    assert map_dataset_name("Bar") == "Bar Dataset"

    # Unknown names pass through unchanged.
    assert map_dataset_name("unknown") == "unknown"
    assert map_dataset_name("test_dataset") == "test_dataset"
    assert map_dataset_name("") == ""
