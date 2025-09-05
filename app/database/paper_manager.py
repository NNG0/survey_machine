import sqlite3
from typing import List, Dict, Any
from MCP.types import Article


class PaperManager:
    """Einfacher Paper Manager für Frontend"""
    
    def __init__(self, db_path: str = "app/database/papers.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Erstelle Tabellen falls sie nicht existieren"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_paper(self, title: str, authors: str = "", abstract: str = "", url: str = "") -> int:
        """Paper hinzufügen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO papers (title, authors, abstract, url) VALUES (?, ?, ?, ?)",
                (title, authors, abstract, url)
            )
            conn.commit()
            return cursor.lastrowid
    
    def delete_paper(self, paper_id: str) -> bool:
        """Paper löschen mit String-ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM papers WHERE id = ?", (int(paper_id),))
                conn.commit()
                return cursor.rowcount > 0
        except:
            return False
    
    def delete_all_papers(self) -> int:
        """Alle Papers löschen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM papers")
            conn.commit()
            return cursor.rowcount
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Alle Papers für Frontend holen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM papers ORDER BY created_at DESC").fetchall()
            
            papers = []
            for row in rows:
                papers.append({
                    "id": str(row["id"]),
                    "title": row["title"],
                    "authors": row["authors"] or "Unknown Authors",
                    "year": 2024,
                    "journal": "Academic Journal",
                    "abstract": row["abstract"] or "No abstract",
                    "relevance": 0,
                    "tags": ["Database"],
                    "citation": f"{row['authors'] or 'Unknown'} (2024). {row['title']}",
                    "doi": row["url"] or "",
                    "savedAt": row["created_at"]
                })
            return papers