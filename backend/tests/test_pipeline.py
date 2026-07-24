"""Unit tests for document extraction and agents."""

import pytest

from backend.agents.pipeline import ContentPipeline, _split_title_body
from backend.models.entities import Platform
from backend.services.ai_client import AIClient, clamp01
from backend.services.documents import detect_document_kind, extract_text
from backend.services.platforms import list_platforms


def test_detect_document_kinds() -> None:
    assert detect_document_kind("a.pdf", "application/pdf") == "pdf"
    assert detect_document_kind("notes.md", "text/plain") == "txt"
    assert detect_document_kind("notes.md", "text/markdown") == "md"
    assert detect_document_kind("data.csv", "text/csv") == "csv"


def test_extract_txt_and_csv() -> None:
    assert extract_text(b"hello world", "txt") == "hello world"
    csv_text = extract_text(b"a,b\n1,2\n", "csv")
    assert "a, b" in csv_text
    assert "1, 2" in csv_text


def test_split_title_body() -> None:
    title, body = _split_title_body("TITLE: Hello\n\nBody text", fallback_title="x")
    assert title == "Hello"
    assert "Body text" in body


def test_clamp01() -> None:
    assert clamp01(1.5) == 1.0
    assert clamp01(-0.2) == 0.0
    assert clamp01(0.4) == 0.4


def test_platforms_catalog() -> None:
    platforms = list_platforms()
    ids = {p.id for p in platforms}
    assert Platform.LINKEDIN in ids
    assert Platform.TWITTER in ids
    assert len(platforms) == 6


@pytest.mark.asyncio
async def test_mock_pipeline_produces_package(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from backend.core.config import get_settings

    get_settings.cache_clear()
    pipeline = ContentPipeline()
    ctx = await pipeline.run(
        prompt=(
            "Write an intermediate LinkedIn post about " "retrieval-augmented generation tradeoffs."
        ),
        platform=Platform.LINKEDIN,
        document_context="RAG reduces hallucination when corpus is curated.",
        image_context="Diagram of embedding search.",
    )
    assert ctx.draft_title
    assert ctx.draft_body
    assert "originality" in ctx.evaluation
    assert "relevance" in ctx.evaluation
    assert "expertise" in ctx.evaluation
    assert ctx.banner_prompt
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_mock_embeddings_similarity() -> None:
    client = AIClient()
    vectors = await client.embed(["same text", "same text", "totally different topic xyz"])
    sim_same = client.cosine_similarity(vectors[0], vectors[1])
    sim_diff = client.cosine_similarity(vectors[0], vectors[2])
    assert sim_same > sim_diff


def test_health_app_import() -> None:
    from backend.main import create_app

    app = create_app()
    assert app.title
