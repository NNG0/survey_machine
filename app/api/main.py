from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import shutil
import os
import sys

sys.path.append("..")
from database.paper_manager import PaperManager

app = FastAPI(title="Survey Machine API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = PaperManager(db_path="database/papers.db")


class PaperCreate(BaseModel):
    title: str
    authors: str = ""
    abstract: str = ""
    url: str = ""
    year: Optional[int] = None
    relevance_score: Optional[float] = None
    cluster_id: Optional[int] = None
    cluster_label: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Survey Machine API"}


@app.get("/papers")
async def get_all_papers():
    """Alle Papers holen"""
    return manager.get_all_papers()


@app.post("/papers")
async def create_paper(paper: PaperCreate):
    """Paper erstellen"""
    paper_id = manager.add_paper(**paper.dict())
    return {"id": paper_id, "message": "Paper created successfully"}


@app.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str):
    """Paper löschen"""
    success = manager.delete_paper(paper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"message": "Paper deleted successfully"}


@app.delete("/papers")
async def delete_all_papers():
    """Alle Papers löschen"""
    count = manager.delete_all_papers()
    return {"message": f"Deleted {count} papers"}


@app.post("/papers/{paper_id}/upload-pdf")
async def upload_pdf(paper_id: int, file: UploadFile = File(...)):
    """PDF für Paper hochladen"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    temp_file = f"temp_{file.filename}"
    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        success = manager.upload_paper_pdf(paper_id, temp_file, file.filename)
        os.remove(temp_file)

        if not success:
            raise HTTPException(status_code=500, detail="Upload failed")
        return {"message": "PDF uploaded successfully"}

    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/papers/{paper_id}/file")
async def get_paper_file(paper_id: int):
    """Dateipfad für Paper holen"""
    file_path = manager.get_paper_file_path(paper_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="No file found for this paper")
    return {"file_path": file_path}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
