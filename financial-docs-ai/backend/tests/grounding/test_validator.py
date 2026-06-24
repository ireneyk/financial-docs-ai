"""Unit tests for citation extraction and grounding."""

from app.assistant.outputs import Citation, GroundedAnswer
from app.grounding.validator import GroundingValidator
from app.retrieval.queries import SourcePassage


def _passage(chunk_id: str, index: int) -> SourcePassage:
    return SourcePassage(
        chunk_id=chunk_id,
        document_id="doc-1",
        ticker="AAPL",
        form_type="10-K",
        filing_date="2024-10-31",
        report_year="2024",
        chunk_index=index,
        text=f"Passage text {index}",
        metadata={},
    )


def test_extract_inline_citations() -> None:
    passages = [_passage("chunk-1", 0), _passage("chunk-2", 1)]
    validator = GroundingValidator()
    citations = validator.extract_inline_citations("Revenue grew [1] and margins [2].", passages)
    assert len(citations) == 2
    assert citations[0].chunk_id == "chunk-1"


def test_validate_rejects_unknown_chunk() -> None:
    validator = GroundingValidator()
    answer = GroundedAnswer(
        answer="Unsupported claim [1].",
        citations=[Citation(chunk_id="missing", label="[1]", excerpt="x", metadata={})],
    )
    passages = [_passage("chunk-1", 0)]

    try:
        validator.validate(answer, passages)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_validate_allows_insufficient_evidence_without_citations() -> None:
    validator = GroundingValidator()
    answer = GroundedAnswer(
        answer="The corpus does not contain enough evidence to answer that question.",
        citations=[],
    )
    result = validator.validate(answer, [_passage("chunk-1", 0)])
    assert result.citations == []
