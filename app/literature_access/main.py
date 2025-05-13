import os
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv


app = FastAPI()

load_dotenv()

OPEN_ALEX_MAIL = os.getenv("OPEN_ALEX_MAIL")
OPEN_ALEX_BASE_URL = "https://api.openalex.org/works?"

@app.get("/")
async def root():
    return {"message": OPEN_ALEX_MAIL}

@app.get("/works")
async def works():
    params = {
        "mailto": OPEN_ALEX_MAIL
    }

    async with httpx.AsyncClient() as client:
        try:
            if OPEN_ALEX_MAIL:
                response = await client.get(OPEN_ALEX_BASE_URL, params = params)
            else:
                response = await client.get(OPEN_ALEX_BASE_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": str(exc)}

    data = response.json()

    return data

@app.get("/search")
async def search_openalex(q: str):
    params = {
        "search": q
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPEN_ALEX_BASE_URL, params = params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": str(exc)}

    data = response.json()
    return {"query":q,"results":data}
