"""Grobid PDF Parser"""

import os
import requests
from typing import Dict
from .base import PDFParser


class GrobidParser(PDFParser):
    """PDF parser using Grobid service"""
    
    def __init__(self):
        # Grobid URL based on Docker environment
        if os.getenv("AM_I_IN_DOCKER", "false") == "true":
            self.grobid_url = "http://grobid:8070"
        else:
            self.grobid_url = "http://localhost:8070"
    
    async def parse_pdf(self, file_path: str) -> Dict[str, str]:
        """Parse PDF using Grobid service"""
        try:
            with open(file_path, 'rb') as pdf_file:
                files = {'input': pdf_file}
                response = requests.post(
                    f"{self.grobid_url}/api/processFulltextDocument",
                    files=files,
                    timeout=120
                )
                
            if response.status_code == 200:
                # Parse Grobid XML response
                xml_content = response.text
                return self._extract_metadata_from_xml(xml_content)
            else:
                raise Exception(f"Grobid request failed: {response.status_code}")
                
        except Exception as e:
            print(f"Grobid parsing failed: {e}")
            # Fallback to filename
            filename = os.path.basename(file_path).replace('.pdf', '')
            return {
                "title": filename,
                "authors": "Unknown",
                "abstract": f"Failed to parse PDF: {str(e)}"
            }
    
    def _extract_metadata_from_xml(self, xml_content: str) -> Dict[str, str]:
        """Extract metadata from Grobid XML response"""
        # Simple XML parsing for title, authors, abstract
        # This is a basic implementation - could be improved with proper XML parsing
        
        title = "Unknown Title"
        authors = "Unknown Authors"
        abstract = ""
        
        try:
            # Extract title
            if '<title level="a" type="main">' in xml_content:
                start = xml_content.find('<title level="a" type="main">') + len('<title level="a" type="main">')
                end = xml_content.find('</title>', start)
                if end > start:
                    title = xml_content[start:end].strip()
            
            # Extract authors (simplified)
            if '<author>' in xml_content:
                authors_list = []
                author_start = 0
                while True:
                    author_pos = xml_content.find('<author>', author_start)
                    if author_pos == -1:
                        break
                    author_end = xml_content.find('</author>', author_pos)
                    if author_end > author_pos:
                        # Very basic author extraction
                        if '<persName>' in xml_content[author_pos:author_end]:
                            name_start = xml_content.find('<persName>', author_pos) + len('<persName>')
                            name_end = xml_content.find('</persName>', name_start)
                            if name_end > name_start:
                                author_name = xml_content[name_start:name_end].strip()
                                # Remove XML tags
                                author_name = author_name.replace('<forename type="first">', '').replace('</forename>', '')
                                author_name = author_name.replace('<surname>', '').replace('</surname>', '')
                                author_name = ' '.join(author_name.split())
                                if author_name:
                                    authors_list.append(author_name)
                    author_start = author_end + 1
                
                if authors_list:
                    authors = ', '.join(authors_list)
            
            # Extract abstract
            if '<abstract>' in xml_content:
                start = xml_content.find('<abstract>') + len('<abstract>')
                end = xml_content.find('</abstract>', start)
                if end > start:
                    abstract = xml_content[start:end].strip()
                    # Remove XML tags from abstract
                    abstract = abstract.replace('<p>', '').replace('</p>', ' ')
                    abstract = ' '.join(abstract.split())
        
        except Exception as e:
            print(f"XML parsing error: {e}")
        
        return {
            "title": title,
            "authors": authors, 
            "abstract": abstract
        }