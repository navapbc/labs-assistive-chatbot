import logging
import time
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Sequence

from src.citations import CitationFactory, create_prompt_context, split_into_subsections
from src.db.models.document import ChunkWithScore, Subsection
from src.format import FormattingConfig
from src.generate import (
    ChatHistory,
    MessageAttributes,
    MessageAttributesT,
    analyze_message,
    generate,
    generate_streaming_async,
)
from src.retrieve import retrieve_with_scores
from src.util.class_utils import all_subclasses

logger = logging.getLogger(__name__)

# Reminder: If your changes are chat-engine-specific, then update the specific `chat_engine.system_prompt_*`.
ANALYZE_MESSAGE_PROMPT = """Analyze the user's message to respond with a JSON dictionary populated with the following fields.

If the user's message is not in English, set translated_message to be an English translation of the user's message. \
Otherwise, set translated_message to be an empty string.

If the question would be easier to answer with additional policy or program context (such as policy documentation), \
set needs_context to True and canned_response to empty string. \
Otherwise, set needs_context to False.
"""

PROMPT = """Provide answers in plain language using http://plainlanguage.gov guidelines.
Write at the average American reading level.
Use bullet points to structure info. Don't use numbered lists.
Keep your answers as similar to your knowledge text as you can.
Respond in the same language as the user's message.
If the user asks for a list of programs or requirements, list them all, don't abbreviate the list. For example "List housing programs available to youth" or "What are the requirements for students to qualify for CalFresh?"

Citations
When referencing the context, do not quote directly. Use the provided citation numbers (e.g., (citation-1)) to indicate when you are drawing from the context. To cite multiple sources at once, you can append citations like so: (citation-1) (citation-2), etc. For example: 'This is a sentence that draws on information from the context.(citation-1)'

Example Answer:
If the client lost their job at no fault, they may be eligible for unemployment insurance benefits. For example: They may qualify if they were laid off due to lack of work.(citation-1) (citation-2) They might be eligible if their hours were significantly reduced.(citation-3)
"""


class OnMessageResult:
    def __init__(
        self,
        response: str,
        system_prompt: str,
        attributes: MessageAttributesT,
        *,
        chunks_with_scores: Sequence[ChunkWithScore] | None = None,
        subsections: Sequence[Subsection] | None = None,
    ):
        self.response = response
        self.subsections = subsections if subsections is not None else []
        self.system_prompt = system_prompt
        self.attributes = attributes
        self.chunks_with_scores = chunks_with_scores if chunks_with_scores is not None else []


class ChatEngineInterface(ABC):
    engine_id: str
    name: str
    llm: str = "gpt-4o"  # Default LLM to use

    # Configuration for formatting responses
    formatting_config: FormattingConfig

    # Thresholds that determine which retrieved documents are shown in the UI
    chunks_shown_max_num: int = 5
    chunks_shown_min_score: float = 0.65

    # Whether to show message-assessment attributes resulting from system_prompt_1 in the UI
    show_msg_attributes: bool = False

    system_prompt_1: str = ANALYZE_MESSAGE_PROMPT
    system_prompt_2: str = PROMPT

    # List of engine-specific configuration settings that can be set by the user.
    # The string elements must match the attribute names for the configuration setting.
    user_settings: list[str]

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def on_message(
        self, question: str, chat_history: Optional[ChatHistory] = None
    ) -> OnMessageResult:
        pass

    @abstractmethod
    async def on_message_streaming(
        self, question: str, chat_history: Optional[ChatHistory] = None
    ) -> tuple[AsyncGenerator[str, None], MessageAttributes, Sequence[Subsection]]:
        pass


def available_engines() -> list[str]:
    return [
        engine_class.engine_id
        for engine_class in all_subclasses(ChatEngineInterface)
        if hasattr(engine_class, "engine_id") and engine_class.engine_id
    ]


def create_engine(engine_id: str) -> ChatEngineInterface | None:
    if engine_id not in available_engines():
        return None

    chat_engine_class = next(
        engine_class
        for engine_class in all_subclasses(ChatEngineInterface)
        if hasattr(engine_class, "engine_id") and engine_class.engine_id == engine_id
    )
    return chat_engine_class()


# Subclasses of ChatEngineInterface can be extracted into a separate file if it gets too large
class BaseEngine(ChatEngineInterface):
    datasets: list[str] = []
    llm: str = "gpt-4o"

    # Thresholds that determine which documents are sent to the LLM
    retrieval_k: int = 8
    retrieval_k_min_score: float = 0.45

    user_settings = [
        "llm",
        "retrieval_k",
        "retrieval_k_min_score",
        "show_msg_attributes",
        "chunks_shown_max_num",
        "chunks_shown_min_score",
        "system_prompt_1",
        "system_prompt_2",
    ]

    formatting_config = FormattingConfig()

    def on_message(
        self, question: str, chat_history: Optional[ChatHistory] = None
    ) -> OnMessageResult:
        # Start timing system_prompt_1
        start_time = time.perf_counter()
        attributes = analyze_message(self.llm, self.system_prompt_1, question, MessageAttributes)
        system_prompt_1_duration = time.perf_counter() - start_time
        logger.info(
            f"System Prompt 1 (analyze_message) took {system_prompt_1_duration:.2f} seconds"
        )

        if attributes.needs_context:
            return self._build_response_with_context(question, attributes, chat_history)

        return self._build_response(question, attributes, chat_history)

    async def on_message_streaming(
        self, question: str, chat_history: Optional[ChatHistory] = None
    ) -> tuple[AsyncGenerator[str, None], MessageAttributes, Sequence[Subsection]]:
        # Start timing system_prompt_1
        start_time = time.perf_counter()
        attributes = analyze_message(self.llm, self.system_prompt_1, question, MessageAttributes)
        system_prompt_1_duration = time.perf_counter() - start_time
        logger.info(
            f"System Prompt 1 (analyze_message) took {system_prompt_1_duration:.2f} seconds"
        )

        # Directly return the result of _build_streaming_response
        return await self._build_streaming_response(question, attributes, chat_history)

    def _build_response(
        self,
        question: str,
        attributes: MessageAttributesT,
        chat_history: Optional[ChatHistory] = None,
    ) -> OnMessageResult:
        # Start timing system_prompt_2
        start_time = time.perf_counter()
        response = generate(
            self.llm,
            self.system_prompt_2,
            question,
            None,
            chat_history,
        )
        system_prompt_2_duration = time.perf_counter() - start_time
        logger.info(
            f"System Prompt 2 (generate without context) took {system_prompt_2_duration:.2f} seconds"
        )

        return OnMessageResult(response, self.system_prompt_2, attributes)

    def _build_response_with_context(
        self,
        question: str,
        attributes: MessageAttributesT,
        chat_history: Optional[ChatHistory] = None,
    ) -> OnMessageResult:
        question_for_retrieval = attributes.translated_message or question

        # Time the retrieval separately since we know it's fast
        retrieval_start = time.perf_counter()
        chunks_with_scores = retrieve_with_scores(
            question_for_retrieval,
            retrieval_k=self.retrieval_k,
            retrieval_k_min_score=self.retrieval_k_min_score,
            datasets=self.datasets,
        )
        retrieval_duration = time.perf_counter() - retrieval_start
        logger.info(f"Vector retrieval took {retrieval_duration:.2f} seconds")

        chunks = [chunk_with_score.chunk for chunk_with_score in chunks_with_scores]
        # Provide a factory to reset the citation id counter
        subsections = split_into_subsections(chunks, factory=CitationFactory())
        context_text = create_prompt_context(subsections)

        # Start timing system_prompt_2
        start_time = time.perf_counter()
        response = generate(
            self.llm,
            self.system_prompt_2,
            question,
            context_text,
            chat_history,
        )
        system_prompt_2_duration = time.perf_counter() - start_time
        logger.info(
            f"System Prompt 2 (generate with context) took {system_prompt_2_duration:.2f} seconds"
        )

        return OnMessageResult(
            response,
            self.system_prompt_2,
            attributes,
            chunks_with_scores=chunks_with_scores,
            subsections=subsections,
        )

    async def _build_streaming_response(
        self,
        question: str,
        attributes: MessageAttributes,
        chat_history: Optional[ChatHistory] = None,
    ) -> tuple[AsyncGenerator[str, None], MessageAttributes, Sequence[Subsection]]:
        """Helper method to build a streaming response with or without context"""
        subsections: Sequence[Subsection] = []

        if attributes.needs_context:
            # Get retrieval question
            question_for_retrieval = attributes.translated_message or question

            # Retrieve context - this is the same code used in _build_response_with_context
            start_time = time.perf_counter()
            chunks_with_scores = retrieve_with_scores(
                question_for_retrieval,
                retrieval_k=self.retrieval_k,
                retrieval_k_min_score=self.retrieval_k_min_score,
                datasets=self.datasets,
            )
            retrieval_duration = time.perf_counter() - start_time
            logger.info(f"Vector retrieval took {retrieval_duration:.2f} seconds")

            # Prepare context
            chunks = [chunk_with_score.chunk for chunk_with_score in chunks_with_scores]
            subsections = split_into_subsections(chunks, factory=CitationFactory())
            context_text = create_prompt_context(subsections)

            # Stream response with context
            generator = generate_streaming_async(
                self.llm,
                self.system_prompt_2,
                question,
                context_text,
                chat_history,
            )
            return generator, attributes, subsections
        else:
            # Stream response without context
            generator = generate_streaming_async(
                self.llm,
                self.system_prompt_2,
                question,
                None,
                chat_history,
            )
            return generator, attributes, subsections


# Import engine subclass modules so they are discovered by available_engines()
import src.engines  # noqa: F401, E402
