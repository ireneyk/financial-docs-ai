"""Reciprocal Rank Fusion for hybrid retrieval."""

from collections import defaultdict


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
    top_n: int = 12,
) -> list[str]:
    scores: dict[str, float] = defaultdict(float)

    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            scores[item_id] += 1.0 / (k + rank)

    return sorted(scores.keys(), key=lambda item_id: scores[item_id], reverse=True)[:top_n]
