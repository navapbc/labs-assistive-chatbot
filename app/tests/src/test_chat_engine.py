import pytest

from src import chat_engine
from src.chat_engine import BaseEngine
from src.engines.example_engine import ExampleEngine
from src.generate import MessageAttributes


def test_available_engines():
    engines = chat_engine.available_engines()
    assert isinstance(engines, list)
    assert len(engines) > 0
    assert "example" in engines


def test_create_engine_example():
    engine = chat_engine.create_engine("example")
    assert engine is not None
    assert isinstance(engine, ExampleEngine)
    assert engine.engine_id == "example"
    assert engine.name == "Example Chat Engine"
    assert engine.datasets == []


def test_create_engine_unknown():
    engine = chat_engine.create_engine("nonexistent-engine")
    assert engine is None


def test_on_message_example_needs_context(monkeypatch):
    monkeypatch.setattr(
        chat_engine,
        "analyze_message",
        lambda *_, **_kw: MessageAttributes(
            needs_context=True,
            users_language="en",
            translated_message="",
        ),
    )
    monkeypatch.setattr(chat_engine, "generate", lambda *_, **_kw: "This is a generated response")
    monkeypatch.setattr(chat_engine, "retrieve_with_scores", lambda *_, **_kw: [])

    engine = chat_engine.create_engine("example")
    result = engine.on_message("What is AI?")
    assert result.response == "This is a generated response"
    assert result.attributes.needs_context is True


def test_on_message_example_no_context(monkeypatch):
    monkeypatch.setattr(
        chat_engine,
        "analyze_message",
        lambda *_, **_kw: MessageAttributes(
            needs_context=False,
            users_language="en",
            translated_message="",
        ),
    )
    monkeypatch.setattr(chat_engine, "generate", lambda *_, **_kw: "This is a generated response")

    engine = chat_engine.create_engine("example")
    result = engine.on_message("What is AI?")
    assert result.response == "This is a generated response"
    assert not result.chunks_with_scores
    assert not result.subsections


@pytest.mark.asyncio
async def test_on_message_streaming_example_with_context(monkeypatch):
    monkeypatch.setattr(
        chat_engine,
        "analyze_message",
        lambda *_, **_kw: MessageAttributes(
            needs_context=True,
            users_language="en",
            translated_message="",
        ),
    )

    async def mock_generate_streaming(*args, **kwargs):
        chunks = ["First chunk", " second chunk", " final chunk"]
        for chunk in chunks:
            yield chunk

    monkeypatch.setattr(chat_engine, "generate_streaming_async", mock_generate_streaming)
    monkeypatch.setattr(chat_engine, "retrieve_with_scores", lambda *_, **_kw: [])

    engine = chat_engine.create_engine("example")
    generator, attributes, subsections = await engine.on_message_streaming("What is AI?")

    chunks = []
    async for chunk in generator:
        chunks.append(chunk)

    assert chunks == ["First chunk", " second chunk", " final chunk"]
    assert attributes.needs_context is True
    assert subsections == []


@pytest.mark.asyncio
async def test_on_message_streaming_example_no_context(monkeypatch):
    monkeypatch.setattr(
        chat_engine,
        "analyze_message",
        lambda *_, **_kw: MessageAttributes(
            needs_context=False,
            users_language="en",
            translated_message="",
        ),
    )

    async def mock_generate_streaming(*args, **kwargs):
        yield "Simple response"

    monkeypatch.setattr(chat_engine, "generate_streaming_async", mock_generate_streaming)

    engine = chat_engine.create_engine("example")
    generator, attributes, subsections = await engine.on_message_streaming("Hello")

    chunks = []
    async for chunk in generator:
        chunks.append(chunk)

    assert chunks == ["Simple response"]
    assert attributes.needs_context is False
    assert subsections == []
