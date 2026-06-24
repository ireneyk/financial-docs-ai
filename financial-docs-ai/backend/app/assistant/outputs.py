"""Typed outputs from the document assistant."""

from pydantic import BaseModel, Field

from app.retrieval.queries import SourcePassage


class Citation(BaseModel):
    chunk_id: str
    label: str
    excerpt: str
    metadata: dict = Field(default_factory=dict)


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    cited_passages: list[SourcePassage] = Field(default_factory=list)
