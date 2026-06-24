"""Unit tests for reciprocal rank fusion."""

from app.retrieval.fusion import reciprocal_rank_fusion


def test_rrf_prefers_items_in_both_lists() -> None:
    fused = reciprocal_rank_fusion(
        [["a", "b", "c"], ["b", "a", "d"]],
        k=60,
        top_n=3,
    )
    assert fused[0] in {"a", "b"}
    assert len(fused) == 3


def test_rrf_respects_top_n() -> None:
    fused = reciprocal_rank_fusion([["x", "y", "z"]], top_n=2)
    assert fused == ["x", "y"]
