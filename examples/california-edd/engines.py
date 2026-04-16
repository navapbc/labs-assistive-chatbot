"""
California EDD chat engine.

This engine is configured for California's Employment Development Department (EDD).
It restricts responses to EDD programs only and uses the CA EDD dataset scraped
from edd.ca.gov.

To use:
  1. Copy this file to app/src/engines/ca_edd_engine.py
  2. Import in app/src/engines/__init__.py:
       import src.engines.ca_edd_engine  # noqa: F401
  3. Set CHAT_ENGINE=ca-edd-web in your environment or app_config.py
"""

from src.chat_engine import PROMPT, BaseEngine


class CaEddWebEngine(BaseEngine):
    engine_id: str = "ca-edd-web"
    name: str = "CA EDD Web Chat Engine"
    datasets: list[str] = ["CA EDD"]

    retrieval_k: int = 50
    retrieval_k_min_score: float = -1

    chunks_shown_min_score: float = -1
    chunks_shown_max_num: int = 8

    system_prompt = f"""You are an assistant to navigators who support clients (such as claimants, beneficiaries, families, and individuals) during the screening, application, and receipt of public benefits from California's Employment Development Department (EDD).
If you can't find information about the user's prompt in your context, don't answer it. If the user asks a question about a program not delivered by California's Employment Development Department (EDD), don't answer beyond pointing the user to the relevant trusted website for more information. Don't answer questions about tax credits (such as EITC, CTC) or benefit programs not delivered by EDD.
If a prompt is about an EDD program, but you can't tell which one, detect and clarify program ambiguity. Ask: "The EDD administers several programs such as State Disability Insurance (SDI), Paid Family Leave (PFL), and Unemployment Insurance (UI). I'm not sure which benefit program your prompt is about; could you let me know?"

{PROMPT}"""
