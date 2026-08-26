"""Brand Knowledge Base RAG helpers.

Ingestion chunks documents, generates embeddings via the configured
embedding provider, and stores them on KnowledgeDocument rows.
Retrieval ranks stored embeddings by cosine similarity against a query.
"""
import logging
import math
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.core.providers.embedding.factory import get_embedding_provider
from app.db.models.marketing import KnowledgeDocument

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def chunk_text(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        # Prefer breaking at paragraph/sentence boundary within the window
        if end < len(text):
            for sep in ("\n\n", "\n", ". "):
                boundary = text.rfind(sep, start + CHUNK_SIZE - 200, end)
                if boundary > start:
                    end = boundary + (2 if sep.endswith(" ") else len(sep))
                    break
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return [c for c in chunks if c]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    provider = get_embedding_provider()
    if provider is None or not texts:
        return []
    result = await provider.embed(texts)
    return result.embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def embed_knowledge_documents(session: AsyncSession, org_id: UUID, title: str, content: str,
                                    source_type: str, source_url: Optional[str] = None,
                                    meta: Optional[dict] = None) -> list[KnowledgeDocument]:
    """Chunk + embed + persist a knowledge document. Returns created rows."""
    chunks = chunk_text(content)
    if not chunks:
        return []

    try:
        embeddings = await embed_texts(chunks)
    except Exception as e:
        logger.warning("Embedding generation failed, storing without vectors: %s", e)
        embeddings = []

    docs: list[KnowledgeDocument] = []
    for i, chunk in enumerate(chunks):
        doc = KnowledgeDocument(
            organization_id=org_id,
            title=title,
            content=chunk,
            source_type=source_type,
            source_url=source_url,
            source_id=str(org_id),
            chunk_index=i,
            total_chunks=len(chunks),
            embedding=embeddings[i] if i < len(embeddings) else None,
            meta=meta or {},
        )
        session.add(doc)
        docs.append(doc)
    await session.commit()
    for d in docs:
        await session.refresh(d)
    return docs


async def search_knowledge(
    session: AsyncSession,
    org_id: UUID,
    query: str,
    top_k: int = 5,
    min_score: float = 0.3,
) -> list[dict]:
    """Semantic search over the brand knowledge base.

    Falls back to naive keyword matching when embeddings are unavailable.
    Returns [{title, content, score, source_type, source_url}] sorted by relevance.
    """
    result = await session.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.organization_id == org_id)
    )
    docs = result.scalars().all()
    if not docs:
        return []

    query_embedding: Optional[list[float]] = None
    embedded_docs = [d for d in docs if d.embedding]
    if embedded_docs:
        try:
            query_embedding = (await embed_texts([query]))[0]
        except Exception as e:
            logger.warning("Query embedding failed, falling back to keyword match: %s", e)

    scored = []
    for doc in docs:
        if query_embedding is not None and doc.embedding:
            score = _cosine_similarity(query_embedding, doc.embedding)
        else:
            q = query.lower().split()
            content = doc.content.lower()
            overlap = sum(1 for term in q if term in content)
            score = overlap / max(len(q), 1)
        if score >= min_score:
            scored.append((score, doc))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            "title": doc.title,
            "content": doc.content,
            "score": round(score, 4),
            "source_type": doc.source_type,
            "source_url": doc.source_url,
        }
        for score, doc in scored[:top_k]
    ]


async def retrieve_brand_context_snippets(session: AsyncSession, org_id: UUID, goal: str,
                                          top_k: int | None = None) -> list[dict]:
    """Retrieve knowledge relevant to the marketing objective for agent context."""
    limit = top_k or settings.RAG_CONTEXT_TOP_K
    try:
        return await search_knowledge(session, org_id, goal, top_k=limit, min_score=0.15)
    except Exception as e:
        logger.warning("RAG context retrieval failed: %s", e)
        return []
