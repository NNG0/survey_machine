"""Hybrid PDF Parser with Grobid primary and Python fallback"""

from __future__ import annotations

import asyncio
from typing import Dict

import requests

from .base import PDFParser
from .grobid_parser import GrobidParser
from .python_parser import PythonParser


class HybridParser(PDFParser):
    """PDF parser that tries Grobid first and augments with a Python fallback."""

    def __init__(self, base_url: str | None = None):
        self.grobid_parser = GrobidParser(base_url)
        self.python_parser = PythonParser()

    async def parse_pdf(self, file_path: str) -> Dict[str, str]:
        """Parse PDF using Grobid, enriching or falling back with Python parsing."""

        grobid_data: Dict[str, str] | None = None
        grobid_error: str | None = None

        if await self._is_grobid_available():
            try:
                grobid_data = await self.grobid_parser.parse_pdf(file_path)
            except Exception as exc:  # pragma: no cover - defensive fallback
                grobid_error = str(exc)
                print(f"Grobid parsing failed with exception: {exc}")
        else:
            print("Grobid not available, skipping Grobid parsing")

        if grobid_data and self._has_meaningful_content(grobid_data):
            if self._is_complete(grobid_data):
                return grobid_data

            python_data = await self.python_parser.parse_pdf(file_path)
            return self._merge_results(grobid_data, python_data)

        python_data = await self.python_parser.parse_pdf(file_path)

        if grobid_error and "Failed to parse PDF" not in python_data.get("abstract", ""):
            python_data["abstract"] = self._append_error_hint(
                python_data.get("abstract", ""), grobid_error
            )

        return python_data

    async def _is_grobid_available(self) -> bool:
        """Check if any Grobid URL is reachable using a quick health check."""

        async def ping(url: str) -> bool:
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    f"{url}/api/isalive",  # type: ignore[arg-type]
                    timeout=3,
                )
                return response.status_code == 200
            except Exception:
                return False

        for url in getattr(self.grobid_parser, "grobid_urls", []):
            if await ping(url):
                return True
        return False

    def _has_meaningful_content(self, result: Dict[str, str]) -> bool:
        """Check if Grobid returned more than its internal fallback."""
        if not result:
            return False

        title = (result.get("title") or "").strip().lower()
        abstract = (result.get("abstract") or "").strip().lower()

        if not title or title.startswith("unknown"):
            return False

        return "failed to parse pdf" not in abstract

    def _is_complete(self, result: Dict[str, str]) -> bool:
        """Determine if Grobid already delivered all relevant fields."""
        return all(self._has_value(result.get(field)) for field in ("title", "authors", "abstract"))

    def _merge_results(
        self,
        primary: Dict[str, str],
        secondary: Dict[str, str],
    ) -> Dict[str, str]:
        """Combine Grobid output with Python fallback, preferring stronger fields."""

        merged = secondary.copy()
        for field in ("title", "authors", "abstract"):
            primary_value = (primary.get(field) or "").strip()
            if self._has_value(primary_value):
                merged[field] = primary_value
            elif field not in merged:
                merged[field] = ""

        return merged

    def _has_value(self, value: str | None) -> bool:
        if not value:
            return False

        lowered = value.strip().lower()
        return lowered not in {
            "",
            "unknown",
            "unknown authors",
            "no abstract",
            "no abstract available",
        }

    def _append_error_hint(self, abstract: str, error: str) -> str:
        abstract = abstract.strip()
        hint = f"Grobid fallback error: {error}"
        if not abstract:
            return hint
        return f"{abstract}\n\n{hint}"
