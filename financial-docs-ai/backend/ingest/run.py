"""Ingest downloaded SEC filings into Supabase."""

from __future__ import annotations

import json
import re
import uuid
from html import unescape
from pathlib import Path

from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import DocumentChunk, SourceDocument
from app.database.session import SessionLocal

CHUNK_SIZE = 1200
DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "downloads"


def html_to_markdown(raw_html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.I | re.S)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(content: str, size: int = CHUNK_SIZE) -> list[str]:
    paragraphs = [part.strip() for part in content.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(paragraph) > size:
            chunks.append(paragraph[:size])
            paragraph = paragraph[size:]
        current = paragraph

    if current:
        chunks.append(current)
    return chunks


def ingest_manifest(session: Session, manifest_path: Path, openai_client: OpenAI) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ingested = 0

    for filing in manifest.get("filings", []):
        local_path = DATA_ROOT / filing["local_path"]
        if not local_path.exists():
            continue

        accession = filing["accession_number"]
        existing = session.execute(
            text("SELECT id FROM source_documents WHERE accession_number = :acc"),
            {"acc": accession},
        ).first()
        if existing:
            continue

        markdown = html_to_markdown(local_path.read_text(encoding="utf-8", errors="ignore"))
        document = SourceDocument(
            id=uuid.uuid4(),
            ticker=filing["ticker"],
            company_name=filing.get("ticker"),
            form_type=filing["form"],
            filing_date=filing["filing_date"],
            report_year=(filing.get("report_date") or filing["filing_date"])[:4],
            accession_number=accession,
            source_url=filing.get("source_url"),
            markdown_content=markdown,
            metadata_json=filing,
        )
        session.add(document)
        session.flush()

        for index, chunk in enumerate(chunk_text(markdown)):
            embedding = openai_client.embeddings.create(
                model=settings.openai_embedding_model,
                input=chunk,
                dimensions=settings.openai_embedding_dimensions,
            ).data[0].embedding

            session.add(
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    chunk_index=index,
                    chunk_text=chunk,
                    token_count=len(chunk.split()),
                    embedding=embedding,
                    metadata_json={
                        "ticker": document.ticker,
                        "form_type": document.form_type,
                        "filing_date": document.filing_date,
                        "report_year": document.report_year,
                    },
                )
            )

        ingested += 1
        session.commit()

    return ingested


def main() -> None:
    manifest_path = DATA_ROOT / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest at {manifest_path}. Run uv run data/download.py first.")

    client = OpenAI(api_key=settings.openai_api_key)
    session = SessionLocal()
    try:
        count = ingest_manifest(session, manifest_path, client)
        print(f"Ingested {count} document(s).")
    finally:
        session.close()


if __name__ == "__main__":
    main()
