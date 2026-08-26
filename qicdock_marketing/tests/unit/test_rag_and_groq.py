"""Unit tests for RAG chunking and Groq provider helpers."""
import pytest

from app.rag.knowledge import chunk_text
from app.core.providers.llm.groq import GroqProvider


class TestChunkText:
    def test_empty(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        assert chunk_text("Short brand note.") == ["Short brand note."]

    def test_long_text_multiple_chunks_within_limit(self):
        text = ("Qicdock product paragraph. " * 400).strip()
        chunks = chunk_text(text)
        assert len(chunks) > 1
        for c in chunks:
            assert 0 < len(c) <= 1700

    def test_no_content_lost(self):
        text = " ".join(f"sentence {i} about qicdock docks." for i in range(300))
        chunks = chunk_text(text)
        assert sum(len(c) for c in chunks) >= len(text) * 0.95


class TestGroqExtractJson:
    def test_plain_json(self):
        assert GroqProvider._extract_json('{"a": 1}') == {"a": 1}

    def test_fenced_json(self):
        assert GroqProvider._extract_json('```json\n{"a": 2}\n```') == {"a": 2}

    def test_json_with_surrounding_text(self):
        assert GroqProvider._extract_json('Here you go: {"a": [1,2]} hope that helps') == {"a": [1, 2]}

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            GroqProvider._extract_json("no json here at all")
