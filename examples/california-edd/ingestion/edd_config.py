"""EDD-specific ingestion config.

Exposes ``build_config`` so it can be loaded by the generic ingest runner via:

    make ingest-runner args="edd \\
        --dataset-label='CA EDD' \\
        --benefit-program=employment \\
        --benefit-region=California \\
        --common-base-url=https://edd.ca.gov/en/ \\
        --config-module=examples.california_edd.ingestion.edd_config \\
        --json_input=path/to/edd_scrapings.json"
"""

import re
from typing import Any

from src.util.ingest_utils import IngestConfig


def _fix_input_markdown(markdown: str) -> str:
    # Fix ellipsis text that causes markdown parsing errors
    # '. . .' is parsed as sublists on the same line
    # in https://edd.ca.gov/en/uibdg/total_and_partial_unemployment_tpu_5/
    markdown = markdown.replace(". . .", "...")

    # Nested sublist '* + California's New Application' created without parent list
    # in https://edd.ca.gov/en/about_edd/eddnext
    markdown = markdown.replace("* + ", "    + ")

    # Blank sublist '* ###" in https://edd.ca.gov/en/unemployment/Employer_Information/
    # Tab labels are parsed into list items with headings; remove them
    markdown = re.sub(r"^\s*\* #+", "", markdown, flags=re.MULTILINE)

    # Blank sublist '* +" in https://edd.ca.gov/en/unemployment/Employer_Information/
    # Empty sublist '4. * ' in https://edd.ca.gov/en/about_edd/your-benefit-payment-options/
    # Remove empty nested sublists
    markdown = re.sub(
        r"^\s*(\w+\.|\*|\+|\-) (\w+\.|\*|\+|\-)\s*$", "", markdown, flags=re.MULTILINE
    )
    return markdown


def _prep_json_item(item: dict[str, Any]) -> None:
    markdown = item.get("main_content", item.get("main_primary", None))
    assert markdown, f"Item {item['url']} has no main_content or main_primary"
    item["markdown"] = _fix_input_markdown(markdown)


def build_config(
    *,
    dataset: str,
    dataset_label: str,
    benefit_program: str,
    benefit_region: str,
    common_base_url: str,
) -> IngestConfig:
    return IngestConfig(
        dataset_label,
        benefit_program,
        benefit_region,
        common_base_url or "https://edd.ca.gov/en/",
        dataset,
        _prep_json_item,
    )
