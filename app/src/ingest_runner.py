import argparse
import importlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from src.app_config import app_config
from src.ingester import ingest_json
from src.util.ingest_utils import IngestConfig, drop_existing_dataset, start_ingestion

logger = logging.getLogger(__name__)


def _default_prep_json_item(item: dict[str, Any]) -> None:
    """Promote common scraped-content fields into the ``markdown`` field expected by the ingester."""
    if "markdown" in item and item["markdown"]:
        return
    markdown = item.get("main_content") or item.get("main_primary")
    if not markdown:
        raise ValueError(
            f"Item {item.get('url', '<unknown>')} has no 'markdown', 'main_content', or 'main_primary' field. "
            "Provide a --config-module with a custom prep_json_item if your scrape uses different field names."
        )
    item["markdown"] = markdown


def _load_config_builder(spec: str) -> Callable[..., IngestConfig]:
    """Import a config-builder callable from ``module.path`` or ``module.path:attr``.

    The callable must accept the same keyword args as :func:`build_ingester_config`
    and return an :class:`IngestConfig`.
    """
    module_name, _, attr = spec.partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, attr or "build_config")


def build_ingester_config(
    dataset: str,
    *,
    dataset_label: Optional[str] = None,
    benefit_program: str = "",
    benefit_region: str = "",
    common_base_url: str = "",
    config_module: Optional[str] = None,
) -> IngestConfig:
    """Build an :class:`IngestConfig` from CLI arguments.

    If ``config_module`` is provided, delegate to that module's builder. Otherwise,
    construct a config from the given flags with a generic ``prep_json_item``
    that maps ``main_content``/``main_primary`` into ``markdown``.
    """
    if config_module:
        builder = _load_config_builder(config_module)
        return builder(
            dataset=dataset,
            dataset_label=dataset_label or dataset,
            benefit_program=benefit_program,
            benefit_region=benefit_region,
            common_base_url=common_base_url,
        )

    return IngestConfig(
        dataset_label or dataset,
        benefit_program,
        benefit_region,
        common_base_url,
        dataset,
        _default_prep_json_item,
    )


def get_ingester_config(dataset: str, args: Optional[argparse.Namespace] = None) -> IngestConfig:
    """Thin wrapper over :func:`build_ingester_config` for CLI use."""
    if args is None:
        return build_ingester_config(dataset)
    return build_ingester_config(
        dataset,
        dataset_label=args.dataset_label,
        benefit_program=args.benefit_program,
        benefit_region=args.benefit_region,
        common_base_url=args.common_base_url,
        config_module=args.config_module,
    )


# Print INFO messages since this is often run from the terminal during local development
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def merge_json_files(json_files: list[str], output_file: str) -> None:
    merged = []
    for json_file in json_files:
        json_items = json.loads(Path(json_file).read_text(encoding="utf-8"))
        logger.info("Loaded %d items from %r", len(json_items), json_file)
        merged.extend(json_items)
    logger.info("Merged %d files into %d items in %r", len(json_files), len(merged), output_file)
    Path(output_file).write_text(json.dumps(merged, indent=2), encoding="utf-8")


def conditionally_consolidate_json_files(json_files: list[str], outfile_prefix: str) -> str:
    if not json_files:
        return ""
    if len(json_files) == 1:
        return json_files[0]

    output_file = f"{outfile_prefix}_combined_scrapings.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    merge_json_files(json_files, output_file)
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest scraped JSON content into the vector DB. "
            "Configure the dataset inline with --dataset-label/--benefit-program/... or "
            "via --config-module for datasets that need custom pre-processing."
        )
    )
    parser.add_argument("dataset", help="Dataset/scraper ID (matches the Scrapy spider name)")
    parser.add_argument(
        "--dataset-label",
        default=None,
        help="Human-readable dataset label shown in citations (defaults to the dataset ID)",
    )
    parser.add_argument("--benefit-program", default="", help="Program tag (e.g., 'employment')")
    parser.add_argument(
        "--benefit-region", default="", help="Region tag (e.g., 'California', 'US')"
    )
    parser.add_argument(
        "--common-base-url",
        default="",
        help="Base URL used to strip common prefixes from document sources",
    )
    parser.add_argument(
        "--config-module",
        default=None,
        help=(
            "Python import path to a module exposing a build_config(...) function "
            "(e.g. 'examples.california_edd.ingestion.edd_config'). Use this for datasets "
            "that need custom prep_json_item logic."
        ),
    )
    parser.add_argument("--json_input", help="path to the JSON file to ingest", action="append")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume ingestion from previous run, skipping existing docs",
    )
    parser.add_argument("--skip_db", action="store_true", help="Skip reading from or writing to DB")
    parser.add_argument(
        "--drop-only", action="store_true", help="Only drop existing dataset; don't ingest"
    )
    args = parser.parse_args(sys.argv[1:])

    config = get_ingester_config(args.dataset, args)

    if args.drop_only:
        with app_config.db_session() as db_session:
            logger.info("Dropping existing dataset %r", config.dataset_label)
            dropped = drop_existing_dataset(db_session, config.dataset_label)
            if dropped:
                logger.warning("Dropped existing dataset %r", config.dataset_label)
            db_session.commit()
        return

    output_file_prefix = os.path.join(config.md_base_dir, config.scraper_dataset)
    json_input = conditionally_consolidate_json_files(args.json_input, output_file_prefix)

    start_ingestion(
        logger,
        ingest_json,
        json_input or f"src/ingestion/{config.scraper_dataset}_scrapings.json",
        config,
        skip_db=args.skip_db,
        resume=args.resume,
    )
