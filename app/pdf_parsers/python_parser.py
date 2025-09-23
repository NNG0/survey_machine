"""Python-based PDF Parser using PyMuPDF (fitz)"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Dict

import fitz  # PyMuPDF

from .base import PDFParser


class PythonParser(PDFParser):
    """PDF parser using pure Python libraries"""

    async def parse_pdf(self, file_path: str) -> Dict[str, str]:
        """Parse PDF using PyMuPDF and extract metadata"""

        return await asyncio.to_thread(self._parse_pdf_sync, file_path)

    def _parse_pdf_sync(self, file_path: str) -> Dict[str, str]:
        doc: fitz.Document | None = None
        try:
            doc = fitz.open(file_path)

            metadata = doc.metadata or {}
            title = (metadata.get("title") or "").strip()
            author = (metadata.get("author") or "").strip()

            text_content = self._collect_text(doc)

            if not title:
                title = self._extract_title_from_text(text_content)

            if not author:
                author = self._extract_authors_from_text(text_content)

            abstract = self._extract_abstract_from_text(text_content)

            if not title:
                title = os.path.basename(file_path).replace(".pdf", "")

            if not author:
                author = "Unknown Authors"

            if not abstract:
                abstract = self._extract_first_paragraph(text_content)

            return {
                "title": title,
                "authors": author,
                "abstract": abstract or "No abstract available",
            }

        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"Python PDF parsing error: {exc}")
            filename = os.path.basename(file_path).replace(".pdf", "")
            return {
                "title": filename,
                "authors": "Unknown Authors",
                "abstract": f"Failed to parse PDF with Python parser: {exc}",
            }
        finally:
            if doc is not None:
                doc.close()

    def _collect_text(self, doc: fitz.Document) -> str:
        """Collect text from the first few pages to infer metadata."""
        text_content = ""
        max_pages = min(5, len(doc))
        for page_index in range(max_pages):
            text_content += doc[page_index].get_text()
        return text_content

    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from PDF text content"""
        lines = text.split('\n')

        # Look for title patterns in first few lines
        for i, line in enumerate(lines[:10]):
            line = line.strip()

            # Skip very short lines or lines with too many uppercase chars
            if len(line) < 10 or len(line) > 200:
                continue

            # Skip lines that look like headers/footers
            if any(word in line.lower() for word in ['page', 'doi:', 'arxiv:', 'www.', 'http']):
                continue

            # Look for title-like formatting
            if self._looks_like_title(line):
                return line

        return ""

    def _looks_like_title(self, line: str) -> bool:
        """Determine if a line looks like a title"""
        # Remove common formatting
        clean_line = re.sub(r'[^\w\s]', '', line).strip()

        # Check length and word count
        words = clean_line.split()
        if len(words) < 2 or len(words) > 20:
            return False

        # Avoid lines with too many numbers or special patterns
        if re.search(r'\d{4}', line):  # Years
            return False

        # Title should have some capital letters
        caps = sum(1 for c in line if c.isupper())
        if caps < 2:
            return False

        return True

    def _extract_authors_from_text(self, text: str) -> str:
        """Extract authors from PDF text content"""
        lines = text.split('\n')

        # Look for author patterns after title
        for line in lines[:20]:
            line = line.strip()

            # Skip empty or very short lines
            if len(line) < 5:
                continue

            # Look for author patterns
            if self._looks_like_authors(line):
                # Clean up author line
                authors = self._clean_authors(line)
                if authors:
                    return authors

        return ""

    def _looks_like_authors(self, line: str) -> bool:
        """Determine if a line looks like author names"""
        # Common author patterns
        author_patterns = [
            r'[A-Z][a-z]+ [A-Z][a-z]+',  # FirstName LastName
            r'[A-Z]\. [A-Z][a-z]+',      # F. LastName
            r'[A-Z][a-z]+, [A-Z]\.',     # LastName, F.
        ]

        for pattern in author_patterns:
            if re.search(pattern, line):
                return True

        # Check for comma-separated names
        if ',' in line and not any(word in line.lower() for word in ['university', 'department', 'email']):
            parts = line.split(',')
            if len(parts) >= 2 and all(len(p.strip()) > 2 for p in parts[:3]):
                return True

        return False

    def _clean_authors(self, author_line: str) -> str:
        """Clean and format author names"""
        # Remove common suffixes/affiliations
        cleaned = re.sub(r'\d+', '', author_line)  # Remove numbers
        cleaned = re.sub(r'[^\w\s,.-]', '', cleaned)  # Keep only basic chars

        # Split by common delimiters
        authors = []
        for delimiter in [',', ' and ', ' & ']:
            if delimiter in cleaned:
                parts = cleaned.split(delimiter)
                authors.extend([p.strip() for p in parts if len(p.strip()) > 2])
                break
        else:
            authors = [cleaned.strip()] if cleaned.strip() else []

        # Limit to reasonable number of authors
        if len(authors) > 5:
            return f"{', '.join(authors[:3])} et al."
        elif authors:
            return ', '.join(authors)

        return ""

    def _extract_abstract_from_text(self, text: str) -> str:
        """Extract abstract from PDF text content"""
        # Look for abstract section
        abstract_patterns = [
            r'(?i)abstract[:\s]*(.+?)(?=\n\s*\n|\n\s*keywords|\n\s*introduction|\n\s*1\.)',
            r'(?i)summary[:\s]*(.+?)(?=\n\s*\n|\n\s*keywords|\n\s*introduction)',
        ]

        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)  # Normalize whitespace
                abstract = re.sub(r'\n+', ' ', abstract)  # Remove newlines

                # Limit length
                return self._trim_text(abstract, 1200)

        return ""

    def _extract_first_paragraph(self, text: str) -> str:
        """Extract first substantial paragraph as fallback abstract"""
        lines = text.split('\n')
        paragraph = ""

        for line in lines:
            line = line.strip()

            # Skip headers, short lines, or lines with too many special chars
            if len(line) < 20 or line.count(' ') < 3:
                continue

            # Avoid lines that look like metadata
            if any(word in line.lower() for word in ['doi:', 'arxiv:', 'page', 'figure', 'table']):
                continue

            # Start building paragraph
            paragraph += line + " "

            # Stop when we have enough content
            if len(paragraph) > 200:
                break

        # Clean and limit
        paragraph = re.sub(r'\s+', ' ', paragraph).strip()
        return self._trim_text(paragraph, 600) if len(paragraph) > 50 else "No abstract available"

    def _trim_text(self, text: str, limit: int) -> str:
        """Trim text to a sensible limit while preserving whole words."""
        if len(text) <= limit:
            return text

        trimmed = text[:limit].rsplit(" ", 1)[0]
        return f"{trimmed.strip()}..."
