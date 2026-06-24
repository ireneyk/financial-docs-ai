"""Citation validation — answers must cite retrieved evidence."""

import re

from app.assistant.outputs import Citation, GroundedAnswer
from app.retrieval.queries import SourcePassage


_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class GroundingValidator:
    def validate(self, answer: GroundedAnswer, passages: list[SourcePassage]) -> GroundedAnswer:
        allowed_ids = {p.chunk_id for p in passages}
        valid_citations: list[Citation] = []

        for citation in answer.citations:
            if citation.chunk_id not in allowed_ids:
                raise ValueError(f"Citation references chunk not in retrieval set: {citation.chunk_id}")
            valid_citations.append(citation)

        cited_passage_ids = {c.chunk_id for c in valid_citations}
        answer.cited_passages = [p for p in passages if p.chunk_id in cited_passage_ids]

        if not self._is_insufficient_evidence_answer(answer.answer) and not valid_citations:
            raise ValueError("Grounded answers must include citations unless evidence is insufficient")

        answer.citations = valid_citations
        return answer

    def extract_inline_citations(self, answer_text: str, passages: list[SourcePassage]) -> list[Citation]:
        indices = {int(match) for match in _CITATION_PATTERN.findall(answer_text)}
        citations: list[Citation] = []
        for index in sorted(indices):
            if index < 1 or index > len(passages):
                continue
            passage = passages[index - 1]
            citations.append(
                Citation(
                    chunk_id=passage.chunk_id,
                    label=f"[{index}]",
                    excerpt=passage.text[:500],
                    metadata=passage.metadata,
                )
            )
        return citations

    def _is_insufficient_evidence_answer(self, text: str) -> bool:
        lowered = text.lower()
        markers = [
            "not enough evidence",
            "does not contain enough",
            "cannot find",
            "no supporting",
            "insufficient evidence",
        ]
        return any(marker in lowered for marker in markers)
