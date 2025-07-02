import httpx
import asyncio
from typing import List, Optional
from MCP.types import Article


async def run_enhanced_openalex_search(
    research_question: str,
    paper_limit: int = 10,
    email: Optional[str] = None
) -> List[Article]:
    """
    Simplified OpenAlex search for the MCP agents
    
    Args:
        research_question: The research question to search for
        paper_limit: Maximum number of papers to return
        email: Optional email for higher rate limits
    
    Returns:
        List of relevant articles
    """
    
    base_url = "https://api.openalex.org/works"
    
    # Build request parameters
    params = {
        "search": research_question,
        "per_page": min(paper_limit, 200),  # OpenAlex max is 200
        "sort": "relevance_score:desc",
    }
    
    if email:
        params["mailto"] = email
    
    try:
        print(f"🔍 Searching OpenAlex: '{research_question}' (limit: {paper_limit})")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            works = data.get("results", [])
            
            print(f"Found {len(works)} works from OpenAlex")
            
            articles = []
            for work in works:
                article = _parse_work_to_article(work)
                if article:
                    articles.append(article)
            
            print(f"Parsed {len(articles)} valid articles")
            return articles
            
    except Exception as e:
        print(f"OpenAlex search error: {e}")
        return []


def _parse_work_to_article(work: dict) -> Optional[Article]:
    """Parse OpenAlex work JSON to Article object"""
    
    try:
        # Extract title
        title = work.get("title", "").strip()
        if not title or len(title) < 10:
            return None
        
        # Extract authors (first 3)
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            if author.get("display_name"):
                authors.append(author["display_name"])
        
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."
        if not author_str:
            author_str = "Unknown authors"
        
        # Extract abstract
        abstract = _extract_abstract(work)
        if not abstract or len(abstract.strip()) < 50:
            return None
        
        # Extract URL (prefer DOI)
        url = work.get("doi") or work.get("id", "")
        
        return Article(
            title=title,
            author=author_str,
            abstract=abstract,
            url=url
        )
        
    except Exception as e:
        return None


def _extract_abstract(work: dict) -> str:
    """Extract abstract from OpenAlex format"""
    
    try:
        # Try regular abstract first
        if work.get("abstract"):
            return work["abstract"]
        
        # Try inverted abstract
        inverted_abstract = work.get("abstract_inverted_index", {})
        if not inverted_abstract:
            return ""
        
        # Reconstruct abstract from inverted index
        word_positions = []
        for word, positions in inverted_abstract.items():
            for pos in positions:
                word_positions.append((pos, word))
        
        # Sort by position and join
        word_positions.sort(key=lambda x: x[0])
        abstract = " ".join([word for _, word in word_positions])
        
        return abstract
        
    except Exception:
        return ""