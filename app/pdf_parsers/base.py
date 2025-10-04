"""Base PDF Parser Interface"""

from abc import ABC, abstractmethod
from typing import Dict


class PDFParser(ABC):
    """Abstract base class for PDF parsers"""

    @abstractmethod
    async def parse_pdf(self, file_path: str) -> Dict[str, str]:
        """
        Parse PDF file and extract metadata

        Returns:
            Dict with keys: title, authors, abstract
        """
        pass
