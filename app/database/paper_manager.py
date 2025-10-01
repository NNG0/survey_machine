import sqlite3
import os
import shutil
import json
import uuid
from typing import List, Dict, Any, Optional


class PaperManager:
    
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_dir = os.getenv("DATABASE_PATH", "app/database")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "papers.db")

            legacy_db = os.path.join("app", "database", "papers.db")
            if not os.path.exists(db_path) and os.path.exists(legacy_db):
                try:
                    shutil.copy2(legacy_db, db_path)
                except OSError:
                    pass

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
                    year INTEGER,
                    file_path TEXT,
                    original_filename TEXT,
                    file_size INTEGER,
                    relevance_score REAL,
                    cluster_id INTEGER,
                    cluster_label TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Workflow Results Tabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_results (
                    id TEXT PRIMARY KEY,
                    research_question TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            try:
                conn.execute(
                    "ALTER TABLE workflow_results ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_results_created_at ON workflow_results(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_results_updated_at ON workflow_results(updated_at)"
            )
            
            conn.commit()
    
    def add_paper(self, title: str, authors: str = "", abstract: str = "", url: str = "", 
                  year: int = None, relevance_score: float = None, cluster_id: int = None, 
                  cluster_label: str = None) -> int:
        """Paper hinzufügen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO papers (title, authors, abstract, url, year, relevance_score, cluster_id, cluster_label) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, authors, abstract, url, year, relevance_score, cluster_id, cluster_label)
            )
            conn.commit()
            return cursor.lastrowid
    
    def delete_paper(self, paper_id: str) -> bool:
        """Paper löschen mit String-ID"""
        try:
            # Erst PDF-Datei löschen falls vorhanden
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Versuche zuerst als Integer-ID, sonst als URL
                try:
                    row = conn.execute("SELECT file_path FROM papers WHERE id = ?", (int(paper_id),)).fetchone()
                except ValueError:
                    row = conn.execute("SELECT file_path FROM papers WHERE url = ?", (paper_id,)).fetchone()

                if row and row["file_path"] and os.path.exists(row["file_path"]):
                    os.remove(row["file_path"])

                # Paper aus DB löschen
                try:
                    cursor = conn.execute("DELETE FROM papers WHERE id = ?", (int(paper_id),))
                except ValueError:
                    cursor = conn.execute("DELETE FROM papers WHERE url = ?", (paper_id,))

                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting paper: {e}")
            return False
    
    def delete_all_papers(self) -> int:
        """Alle Papers löschen (inkl. PDFs)"""
        try:
            # Erst alle PDF-Dateien löschen
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT file_path FROM papers WHERE file_path IS NOT NULL").fetchall()
                
                for row in rows:
                    if row["file_path"] and os.path.exists(row["file_path"]):
                        os.remove(row["file_path"])
                
                # Dann alle Papers aus DB löschen
                cursor = conn.execute("DELETE FROM papers")
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error deleting all papers: {e}")
            return 0
    
    def upload_paper_pdf(self, paper_id: int, pdf_file, original_filename: str) -> bool:
        """PDF für ein Paper hochladen"""
        try:
            # Uploads-Ordner erstellen falls nicht vorhanden
            uploads_dir = "uploads/papers"
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Eindeutigen Dateinamen generieren
            unique_filename = f"{paper_id}_{original_filename}"
            file_path = os.path.join(uploads_dir, unique_filename)
            
            # Datei speichern
            shutil.copy2(pdf_file, file_path)
            file_size = os.path.getsize(file_path)
            
            # DB aktualisieren
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE papers SET file_path = ?, original_filename = ?, file_size = ? WHERE id = ?",
                    (file_path, original_filename, file_size, paper_id)
                )
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error uploading PDF: {e}")
            return False

    def get_paper_file_path(self, paper_id: int) -> str:
        """Dateipfad für ein Paper holen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT file_path FROM papers WHERE id = ?", (paper_id,)).fetchone()
            return row["file_path"] if row and row["file_path"] else None
    
    def get_all_papers(self) -> List[Dict[str, Any]]:
        """Alle Papers für Frontend holen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM papers ORDER BY created_at DESC").fetchall()
            
            papers = []
            for row in rows:
                # Check if PDF file exists
                has_pdf = False
                if row["file_path"] and os.path.exists(row["file_path"]):
                    has_pdf = True
                
                papers.append({
                    "id": str(row["id"]),
                    "title": row["title"],
                    "authors": row["authors"] or "Unknown Authors",
                    "year": row["year"] or 2024,
                    "abstract": row["abstract"] or "No abstract",
                    "relevance": row["relevance_score"] or 0,
                    "tags": [row["cluster_label"]] if row["cluster_label"] else [],
                    "citation": f"{row['authors'] or 'Unknown'} ({row['year'] or 2024}). {row['title']}",
                    "doi": row["url"] or "",
                    "savedAt": row["created_at"],
                    "file_path": row["file_path"],
                    "original_filename": row["original_filename"],
                    "file_size": row["file_size"],
                    "has_pdf": has_pdf,
                    "cluster_id": row["cluster_id"],
                    "cluster_label": row["cluster_label"]
                })
            return papers
    
    # def get_papers_by_cluster(self, cluster_id: int) -> List[Dict[str, Any]]:
    #     """Alle Papers eines Clusters holen"""
    #     with sqlite3.connect(self.db_path) as conn:
    #         conn.row_factory = sqlite3.Row
    #         rows = conn.execute(
    #             "SELECT * FROM papers WHERE cluster_id = ? ORDER BY relevance_score DESC", 
    #             (cluster_id,)
    #         ).fetchall()
            
    #         papers = []
    #         for row in rows:
    #             has_pdf = False
    #             if row["file_path"] and os.path.exists(row["file_path"]):
    #                 has_pdf = True
                
    #             papers.append({
    #                 "id": str(row["id"]),
    #                 "title": row["title"],
    #                 "authors": row["authors"] or "Unknown Authors",
    #                 "year": row["year"] or 2024,
    #                 "abstract": row["abstract"] or "No abstract",
    #                 "relevance": row["relevance_score"] or 0,
    #                 "tags": [row["cluster_label"]] if row["cluster_label"] else [],
    #                 "citation": f"{row['authors'] or 'Unknown'} ({row['year'] or 2024}). {row['title']}",
    #                 "doi": row["url"] or "",
    #                 "savedAt": row["created_at"],
    #                 "file_path": row["file_path"],
    #                 "original_filename": row["original_filename"],
    #                 "file_size": row["file_size"],
    #                 "has_pdf": has_pdf,
    #                 "cluster_id": row["cluster_id"],
    #                 "cluster_label": row["cluster_label"]
    #             })
    #         return papers
    
    # def get_clusters_summary(self) -> List[Dict[str, Any]]:
    #     """Cluster-Übersicht mit Anzahl Papers pro Cluster"""
    #     with sqlite3.connect(self.db_path) as conn:
    #         conn.row_factory = sqlite3.Row
    #         rows = conn.execute("""
    #             SELECT 
    #                 cluster_id, 
    #                 cluster_label, 
    #                 COUNT(*) as paper_count,
    #                 AVG(relevance_score) as avg_relevance
    #             FROM papers 
    #             WHERE cluster_id IS NOT NULL 
    #             GROUP BY cluster_id, cluster_label
    #             ORDER BY paper_count DESC
    #         """).fetchall()
            
    #         clusters = []
    #         for row in rows:
    #             clusters.append({
    #                 "cluster_id": row["cluster_id"],
    #                 "cluster_label": row["cluster_label"],
    #                 "paper_count": row["paper_count"],
    #                 "avg_relevance": round(row["avg_relevance"], 3) if row["avg_relevance"] else 0
    #             })
    #         return clusters
    
    # Workflow Results Management
    def upsert_workflow_result(
        self, result_id: str | None, request_status_dict: dict
    ) -> str:
        """Insert or update a workflow result."""

        hydrated_id = result_id or str(uuid.uuid4())
        research_question = (
            request_status_dict.get("settings", {}).get("research_question", "Unknown")
        )
        result_json = json.dumps(request_status_dict, default=str)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO workflow_results (id, research_question, result_data)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    research_question = excluded.research_question,
                    result_data = excluded.result_data,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (hydrated_id, research_question, result_json),
            )
            conn.commit()

        return hydrated_id

    def save_workflow_result(self, request_status_dict: dict) -> str:
        """Backward compatible helper to persist a workflow result."""

        return self.upsert_workflow_result(None, request_status_dict)
    
    def get_all_workflow_results(self) -> List[Dict[str, Any]]:
        """Get all workflow results for frontend"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, research_question, result_data, created_at, updated_at FROM workflow_results ORDER BY updated_at DESC"
            ).fetchall()
            
            results = []
            for row in rows:
                try:
                    result_data = json.loads(row["result_data"])
                    results.append({
                        "id": row["id"],
                        "research_question": row["research_question"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "papers": result_data.get("papers", []),
                        "key_questions": result_data.get("key_questions", []),
                        "result": result_data.get("result", [])
                    })
                except json.JSONDecodeError:
                    # Skip malformed entries
                    continue
            
            return results
    
    def get_workflow_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get specific workflow result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM workflow_results WHERE id = ?", (result_id,)
            ).fetchone()
            
            if row:
                try:
                    return {
                        "id": row["id"],
                        "research_question": row["research_question"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "request_status": json.loads(row["result_data"])
                    }
                except json.JSONDecodeError:
                    return None
            return None

    def get_latest_workflow_result(self) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM workflow_results ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()

            if not row:
                return None

            try:
                return {
                    "id": row["id"],
                    "research_question": row["research_question"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "request_status": json.loads(row["result_data"]),
                }
            except json.JSONDecodeError:
                return None
