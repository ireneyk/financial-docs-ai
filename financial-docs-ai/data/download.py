# /// script
# requires-python = ">=3.12"
# ///
"""Pull a small 10-K sample from SEC EDGAR into data/downloads/."""

from __future__ import annotations

import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib import request

# --- tweak these before running: uv run data/download.py ---
USER_AGENT = "DocumentCopilot your.email@example.com"
TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
FILINGS_PER_COMPANY = 5
OUTPUT_DIR = Path(__file__).resolve().parent / "downloads"
CLEAR_OUTPUT_DIR = True

CIK_BY_TICKER = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
}


def fetch_json(url: str) -> dict:
    req = request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    req = request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "User-Agent": USER_AGENT,
        },
    )
    with request.urlopen(req, timeout=60) as resp:
        return resp.read()


def pick_10k_filings(submission: dict, years: set[str]) -> list[dict[str, str]]:
    recent = submission["filings"]["recent"] if "filings" in submission else submission
    hits: list[dict[str, str]] = []

    for form, accession, document, filed, reported in zip(
        recent["form"],
        recent["accessionNumber"],
        recent["primaryDocument"],
        recent["filingDate"],
        recent["reportDate"],
        strict=True,
    ):
        year = (reported or filed)[:4]
        if form == "10-K" and year in years:
            hits.append(
                {
                    "year": year,
                    "form": form,
                    "accession_number": accession,
                    "primary_document": document,
                    "filing_date": filed,
                    "report_date": reported,
                }
            )
    return hits


def download_corpus() -> dict:
    if CLEAR_OUTPUT_DIR and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC)
    target_years = {str(y) for y in range(now.year - FILINGS_PER_COMPANY, now.year)}

    manifest: dict = {
        "source": "SEC EDGAR",
        "generated_at_utc": now.isoformat(),
        "form": "10-K",
        "downloaded_count": 0,
        "filings": [],
    }

    for ticker in TICKERS:
        print(f"Fetching {ticker}…")
        cik = CIK_BY_TICKER[ticker]
        root = fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json")

        submissions = [root]
        for file_ref in root.get("filings", {}).get("files", []):
            submissions.append(fetch_json(f"https://data.sec.gov/submissions/{file_ref['name']}"))

        filings: list[dict[str, str]] = []
        for submission in submissions:
            filings.extend(pick_10k_filings(submission, target_years))
            if len(filings) >= FILINGS_PER_COMPANY:
                break

        for filing in filings[:FILINGS_PER_COMPANY]:
            accession_path = filing["accession_number"].replace("-", "")
            url = (
                "https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession_path}/{filing['primary_document']}"
            )
            year_dir = OUTPUT_DIR / filing["year"]
            year_dir.mkdir(parents=True, exist_ok=True)
            suffix = Path(filing["primary_document"]).suffix or ".html"
            filename = (
                f"{ticker.lower()}_{filing['form'].lower()}_"
                f"{filing['filing_date']}_{filing['accession_number']}{suffix}"
            )
            dest = year_dir / filename
            dest.write_bytes(fetch_bytes(url))

            manifest["filings"].append(
                {
                    "ticker": ticker,
                    "cik": cik,
                    "form": filing["form"],
                    "filing_date": filing["filing_date"],
                    "report_date": filing["report_date"],
                    "accession_number": filing["accession_number"],
                    "primary_document": filing["primary_document"],
                    "source_url": url,
                    "local_path": str(dest.relative_to(OUTPUT_DIR)),
                }
            )
            manifest["downloaded_count"] += 1
            time.sleep(0.2)

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = download_corpus()
    print(f"Done — {result['downloaded_count']} filing(s) in {OUTPUT_DIR}")
    print(f"Manifest: {OUTPUT_DIR / 'manifest.json'}")
