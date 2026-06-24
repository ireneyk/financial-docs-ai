"""AI SDK data-stream encoding for FastAPI streaming responses."""

import json
from collections.abc import AsyncIterator


def encode_text_delta(text: str) -> bytes:
    return f"0:{json.dumps(text)}\n".encode("utf-8")


def encode_data(payload: dict) -> bytes:
    return f"2:{json.dumps([payload])}\n".encode("utf-8")


async def stream_text_chunks(chunks: list[str]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield encode_text_delta(chunk)


async def stream_plain_text(text: str, chunk_size: int = 24) -> AsyncIterator[bytes]:
    for start in range(0, len(text), chunk_size):
        yield encode_text_delta(text[start:start + chunk_size])
