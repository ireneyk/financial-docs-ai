"""Hybrid semantic + keyword retrieval over document chunks."""

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.database.documents import fulltext_search, get_chunks_by_ids, get_document, vector_search
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import RetrievalResult, SourcePassage


class DocumentRetriever:
    def __init__(self, session: Session, openai_client: AsyncOpenAI | None = None) -> None:
        self._session = session
        self._openai = openai_client or AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed_query(self, query: str) -> list[float]:
        response = await self._openai.embeddings.create(
            model=settings.openai_embedding_model,
            input=query,
            dimensions=settings.openai_embedding_dimensions,
        )
        return response.data[0].embedding

    async def retrieve(self, query: str) -> RetrievalResult:
        embedding = await self.embed_query(query)
        vector_hits = vector_search(self._session, embedding, settings.retrieval_top_k)
        keyword_hits = fulltext_search(self._session, query, settings.retrieval_top_k)

        fused_ids = reciprocal_rank_fusion(
            [[str(c.id) for c in vector_hits], [str(c.id) for c in keyword_hits]],
            k=settings.rrf_k,
            top_n=settings.retrieval_top_k,
        )
        chunks = get_chunks_by_ids(self._session, fused_ids)
        passages = [self._to_passage(chunk) for chunk in chunks]
        return RetrievalResult(query=query, passages=passages)

    def _to_passage(self, chunk) -> SourcePassage:
        document = get_document(self._session, chunk.document_id)
        meta = dict(chunk.metadata_json or {})
        if document is not None:
            meta.setdefault("accession_number", document.accession_number)
            meta.setdefault("company_name", document.company_name)
        return SourcePassage(
            chunk_id=str(chunk.id),
            document_id=str(chunk.document_id),
            ticker=document.ticker if document else meta.get("ticker", ""),
            form_type=document.form_type if document else meta.get("form_type", ""),
            filing_date=document.filing_date if document else meta.get("filing_date", ""),
            report_year=document.report_year if document else meta.get("report_year", ""),
            chunk_index=chunk.chunk_index,
            text=chunk.chunk_text,
            metadata=meta,
        )
