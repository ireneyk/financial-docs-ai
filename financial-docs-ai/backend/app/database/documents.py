"""Source document and chunk query helpers."""

import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database.models import DocumentChunk, SourceDocument


def get_chunk(session: Session, chunk_id: str) -> DocumentChunk | None:
    return session.get(DocumentChunk, uuid.UUID(chunk_id))


def get_chunks_by_ids(session: Session, chunk_ids: list[str]) -> list[DocumentChunk]:
    if not chunk_ids:
        return []
    ids = [uuid.UUID(cid) for cid in chunk_ids]
    stmt = select(DocumentChunk).where(DocumentChunk.id.in_(ids))
    rows = list(session.scalars(stmt))
    by_id = {row.id: row for row in rows}
    return [by_id[cid] for cid in ids if cid in by_id]


def vector_search(session: Session, embedding: list[float], limit: int) -> list[DocumentChunk]:
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(DocumentChunk.embedding.cosine_distance(embedding))
        .limit(limit)
    )
    return list(session.scalars(stmt))


def fulltext_search(session: Session, query: str, limit: int) -> list[DocumentChunk]:
    stmt = text(
        """
        SELECT id
        FROM document_chunks
        WHERE search_vector @@ plainto_tsquery('english', :query)
        ORDER BY ts_rank(search_vector, plainto_tsquery('english', :query)) DESC
        LIMIT :limit
        """
    )
    rows = session.execute(stmt, {"query": query, "limit": limit}).fetchall()
    ids = [str(row[0]) for row in rows]
    return get_chunks_by_ids(session, ids)


def get_surrounding_chunks(session: Session, chunk: DocumentChunk, window: int = 1) -> list[DocumentChunk]:
    low = max(0, chunk.chunk_index - window)
    high = chunk.chunk_index + window
    stmt = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == chunk.document_id,
            DocumentChunk.chunk_index >= low,
            DocumentChunk.chunk_index <= high,
        )
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(session.scalars(stmt))


def get_document(session: Session, document_id: uuid.UUID) -> SourceDocument | None:
    return session.get(SourceDocument, document_id)
