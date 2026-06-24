"""Typed shapes for retrieval results."""

from pydantic import BaseModel, Field


class SourcePassage(BaseModel):
    chunk_id: str
    document_id: str
    ticker: str
    form_type: str
    filing_date: str
    report_year: str
    chunk_index: int
    text: str
    metadata: dict = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    query: str
    passages: list[SourcePassage]
