"""
EDD-specific ingestion runner.

This shows how to configure ingestion for edd.ca.gov content scraped by edd_spider.py.
Copy this into app/src/ingest_runner.py (or merge the edd_config function into your
existing ingest_runner.py) and add an "edd" case to get_ingester_config().

Usage:
    poetry run ingest-runner edd --json_input path/to/edd_scrapings.json
"""

import re

from src.util.ingest_utils import IngestConfig


def edd_config(
    dataset_label: str, benefit_program: str, benefit_region: str, scraper_dataset: str
) -> IngestConfig:
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

    def prep_json_item(item: dict[str, str]) -> None:
        markdown = item.get("main_content", item.get("main_primary", None))
        assert markdown, f"Item {item['url']} has no main_content or main_primary"
        item["markdown"] = _fix_input_markdown(markdown)

    return IngestConfig(
        dataset_label,
        benefit_program,
        benefit_region,
        "https://edd.ca.gov/en/",
        scraper_dataset,
        prep_json_item,
    )


# Example usage in get_ingester_config():
#
# case "edd":
#     return edd_config("CA EDD", "employment", "California", scraper_dataset)
