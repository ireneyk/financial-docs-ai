"""Runtime dependencies passed into the PydanticAI agent."""

from dataclasses import dataclass

from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever


@dataclass
class DocumentAgentDeps:
    user_id: str
    thread_id: str
    retriever: DocumentRetriever
    grounding_validator: GroundingValidator
