import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from src import ingest_runner
from src.ingest_runner import (
    _default_prep_json_item,
    _load_config_builder,
    build_ingester_config,
    get_ingester_config,
    main,
)
from src.util.ingest_utils import IngestConfig

FILE_1_JSON_OBJS = [
    {
        "url": "https://www.ssa.gov/pubs/EN-05-10095.pdf#page=5",
        "title": "Working While Disabled p5",
        "md_file": "ssa_extra_md/EN-05-10095/page05.md",
    },
    {
        "url": "https://www.ssa.gov/pubs/EN-05-10095.pdf#page=7",
        "title": "Working While Disabled p7",
        "md_file": "ssa_extra_md/EN-05-10095/page07.md",
    },
    {
        "url": "https://www.ssa.gov/pubs/EN-05-10095.pdf#page=9",
        "title": "Working While Disabled p9",
        "md_file": "ssa_extra_md/EN-05-10095/page09.md",
    },
]

FILE_2_JSON_OBJS = [
    {
        "url": "https://edd.ca.gov/en/disability/options_to_file_for_di_benefits/",
        "title": "Options to File for Disability Insurance Benefits",
        "markdown": "Disability Insurance (DI) provides short-term, partial wage replacement ...",
        "extra_fields": "## Nonindustrial Disability Insurance\n\nGet answers to FAQs about Nonindustrial Disability Insurance.",
    },
    {
        "url": "https://edd.ca.gov/en/jobs_and_training/northern_region/",
        "title": "The Northern Job Fairs and Workshops",
        "main_primary": "## Scheduled Events\n\n",
    },
]


@pytest.fixture
def json_file_1(tmp_path):
    file_path = tmp_path / "json_file_1.json"
    file_path.write_text(json.dumps(FILE_1_JSON_OBJS), encoding="utf-8")
    return str(file_path)


@pytest.fixture
def json_file_2(tmp_path):
    file_path = tmp_path / "json_file_2.json"
    file_path.write_text(json.dumps(FILE_2_JSON_OBJS), encoding="utf-8")
    return str(file_path)


def patch_ingest_runner(monkeypatch):
    monkeypatch.setattr(
        ingest_runner,
        "get_ingester_config",
        lambda dataset, args=None: IngestConfig(
            "Test ingest runner", "", "", "https://test.org/", "test_ingest_runner"
        ),
    )

    mock_start_ingestion = Mock()
    monkeypatch.setattr(ingest_runner, "start_ingestion", mock_start_ingestion)
    return mock_start_ingestion


def test_main__combine_jsons(monkeypatch, json_file_1, json_file_2):
    mock_start_ingestion = patch_ingest_runner(monkeypatch)

    sys.argv = [
        "ingest_runner",
        "test_ingest_runner",
        f"--json_input={json_file_1}",
        f"--json_input={json_file_2}",
        "--skip_db",
    ]
    main()

    combined_file = mock_start_ingestion.call_args.args[2]
    json_items = json.loads(Path(combined_file).read_text(encoding="utf-8"))
    assert len(json_items) == 5
    for item in FILE_1_JSON_OBJS + FILE_2_JSON_OBJS:
        assert item in json_items


def test_main__1_json_file(monkeypatch, json_file_1):
    mock_start_ingestion = patch_ingest_runner(monkeypatch)

    sys.argv = [
        "ingest_runner",
        "test_ingest_runner",
        f"--json_input={json_file_1}",
        "--skip_db",
    ]
    main()

    assert mock_start_ingestion.call_args.args[2] == json_file_1


def test_main__default_json_file(monkeypatch):
    mock_start_ingestion = patch_ingest_runner(monkeypatch)

    sys.argv = [
        "ingest_runner",
        "test_ingest_runner",
        "--skip_db",
    ]
    main()

    assert (
        mock_start_ingestion.call_args.args[2] == "src/ingestion/test_ingest_runner_scrapings.json"
    )


def test_default_prep_json_item__passthrough():
    item = {"markdown": "already set"}
    _default_prep_json_item(item)
    assert item["markdown"] == "already set"


def test_default_prep_json_item__promotes_main_content():
    item = {"main_content": "body"}
    _default_prep_json_item(item)
    assert item["markdown"] == "body"


def test_default_prep_json_item__promotes_main_primary():
    item = {"main_primary": "body"}
    _default_prep_json_item(item)
    assert item["markdown"] == "body"


def test_default_prep_json_item__raises_when_no_content():
    with pytest.raises(ValueError, match="has no 'markdown'"):
        _default_prep_json_item({"url": "https://example.com/x"})


def test_build_ingester_config__defaults():
    config = build_ingester_config("my_dataset")
    assert config.dataset_label == "my_dataset"
    assert config.scraper_dataset == "my_dataset"
    assert config.prep_json_item is _default_prep_json_item


def test_build_ingester_config__with_config_module(monkeypatch):
    def fake_builder(**kwargs):
        return IngestConfig(
            kwargs["dataset_label"], "", "", kwargs["common_base_url"], kwargs["dataset"]
        )

    monkeypatch.setattr(ingest_runner, "_load_config_builder", lambda spec: fake_builder)
    config = build_ingester_config(
        "my_dataset",
        dataset_label="My Label",
        common_base_url="https://x/",
        config_module="some.module",
    )
    assert config.dataset_label == "My Label"


def test_get_ingester_config__no_args():
    config = get_ingester_config("my_dataset")
    assert config.dataset_label == "my_dataset"


def test_load_config_builder(monkeypatch):
    import types

    fake_module = types.ModuleType("fake_builder_module")
    fake_module.build_config = lambda **kw: "default-builder"
    fake_module.custom = lambda **kw: "custom-builder"
    monkeypatch.setitem(sys.modules, "fake_builder_module", fake_module)

    assert _load_config_builder("fake_builder_module")() == "default-builder"
    assert _load_config_builder("fake_builder_module:custom")() == "custom-builder"
