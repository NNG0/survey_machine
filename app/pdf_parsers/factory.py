"""PDF Parser Factory"""

from __future__ import annotations

import os

from .base import PDFParser
from .grobid_parser import GrobidParser
from .hybrid_parser import HybridParser
from .python_parser import PythonParser


def get_pdf_parser(parser_type: str | None = None) -> PDFParser:
    parser_name = (parser_type or os.getenv("PDF_PARSER", "hybrid")).lower()

    if parser_name == "python":
        print("Using Python PDF parser")
        return PythonParser()

    if parser_name == "grobid":
        print("Using Grobid PDF parser")
        return GrobidParser(base_url=_resolve_grobid_base_url())

    if parser_name == "hybrid":
        print("Using Hybrid PDF parser (Grobid + Python fallback)")
        return HybridParser(base_url=_resolve_grobid_base_url())

    print(f"Unknown parser '{parser_name}', falling back to hybrid")
    return HybridParser(base_url=_resolve_grobid_base_url())


def _resolve_grobid_base_url() -> str:
    is_in_docker = os.getenv("AM_I_IN_DOCKER", "false") == "true"
    host_override = os.getenv("GROBID_HOST")

    if host_override:
        grobid_host = host_override
    else:
        grobid_host = "grobid" if is_in_docker else "localhost"

    port_override = os.getenv("GROBID_PORT")
    if port_override:
        grobid_port = int(port_override)
    else:
        if host_override and host_override in {
            "localhost",
            "127.0.0.1",
            "host.docker.internal",
        }:
            grobid_port = 8090
        elif is_in_docker:
            grobid_port = 8070
        else:
            grobid_port = 8090
    return f"http://{grobid_host}:{grobid_port}"
