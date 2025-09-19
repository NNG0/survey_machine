"""PDF Parser Factory"""

import os
from .base import PDFParser
from .grobid_parser import GrobidParser


def get_pdf_parser(parser_type: str | None = None) -> PDFParser:
    """Return the configured PDF parser.

    Currently only the Grobid parser is supported. Any other configuration
    silently falls back to Grobid so existing environment settings do not
    crash the service.
    """

    parser_name = (parser_type or os.getenv("PDF_PARSER", "grobid")).lower()
    if parser_name != "grobid":
        print(f"Unsupported parser '{parser_name}', falling back to Grobid")

    return GrobidParser()
