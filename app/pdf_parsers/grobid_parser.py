"""Grobid PDF Parser"""

import os
import requests
import xml.etree.ElementTree as ET
from typing import Dict
from .base import PDFParser


class GrobidParser(PDFParser):
    """PDF parser using Grobid service"""

    def __init__(self, base_url: str | None = None):
        if base_url:
            # Wenn man explizit eine URL übergibt
            self.grobid_urls = [base_url]
        elif os.getenv("AM_I_IN_DOCKER", "false") == "true":
            # Reihenfolge: Docker intern → evtl. alternative Ports → Host
            host_override = os.getenv("GROBID_HOST")
            self.grobid_urls = ["http://host.docker.internal:8070"]
            if host_override:
                self.grobid_urls.insert(0, f"http://{host_override}:8070")
        else:
            # Lokal immer Port 8090
            self.grobid_urls = ["http://localhost:8090"]

    async def parse_pdf(self, file_path: str) -> Dict[str, str]:
        """Parse PDF using Grobid service with fallback URLs"""
        last_error = None
        for url in self.grobid_urls:
            try:
                with open(file_path, "rb") as pdf_file:
                    files = {"input": pdf_file}
                    response = requests.post(
                        f"{url}/api/processFulltextDocument",
                        files=files,
                        timeout=240,
                    )
                if response.status_code == 200:
                    return self._extract_metadata_from_xml(response.text)
                else:
                    last_error = (
                        f"Grobid request failed: {response.status_code} at {url}"
                    )
            except Exception as e:
                last_error = f"{url} → {e}"
                print(f"Grobid parsing failed on {url}: {e}")

        # Fallback: Dateiname
        filename = os.path.basename(file_path).replace(".pdf", "")
        return {
            "title": filename,
            "authors": "Unknown",
            "abstract": f"Failed to parse PDF (last error: {last_error})",
        }

    def _extract_metadata_from_xml(self, xml_content: str) -> Dict[str, str]:
        """Extract metadata from Grobid XML response using proper XML parsing"""
        try:
            root = ET.fromstring(xml_content)
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}

            # Titel
            title = "Unknown Title"
            title_el = root.find(".//tei:titleStmt/tei:title[@type='main']", ns)
            if title_el is None:
                title_el = root.find(".//tei:title[@level='a'][@type='main']", ns)
            if title_el is None:
                title_el = root.find(".//tei:title", ns)
            if title_el is not None and title_el.text:
                title = title_el.text.strip()

            # Autoren
            authors = []
            for author in root.findall(".//tei:titleStmt/tei:author", ns):
                name_parts = []
                for el in author.findall(".//tei:forename", ns) + author.findall(
                    ".//tei:surname", ns
                ):
                    if el.text:
                        name_parts.append(el.text.strip())
                name = " ".join(name_parts)
                if name:
                    authors.append(name)

            if not authors:
                for author in root.findall(".//tei:sourceDesc//tei:author", ns):
                    name_parts = []
                    for el in author.findall(".//tei:forename", ns) + author.findall(
                        ".//tei:surname", ns
                    ):
                        if el.text:
                            name_parts.append(el.text.strip())
                    name = " ".join(name_parts)
                    if name:
                        authors.append(name)

            if len(authors) > 5:
                authors_str = ", ".join(authors[:3]) + " et al."
            elif authors:
                authors_str = ", ".join(authors)
            else:
                authors_str = "Unknown Authors"

            # Abstract
            abstract = ""
            abstract_el = root.find(".//tei:abstract", ns)
            if abstract_el is not None:
                abstract = "".join(abstract_el.itertext()).strip()

            return {"title": title, "authors": authors_str, "abstract": abstract}

        except Exception as e:
            print(f"XML parsing error: {e}")
            return {
                "title": "Unknown Title",
                "authors": "Unknown Authors",
                "abstract": f"Failed to parse XML: {str(e)}",
            }
