import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv


mcp = FastMCP("literature-access")

load_dotenv()

OPEN_ALEX_MAIL = os.getenv("OPEN_ALEX_MAIL")
OPEN_ALEX_BASE_URL = "https://api.openalex.org/works?"

# @app.get("/")
# async def root():
#     return {"message": OPEN_ALEX_MAIL}


@mcp.tool()
async def works():
    params = {"mailto": OPEN_ALEX_MAIL}

    async with httpx.AsyncClient() as client:
        try:
            if OPEN_ALEX_MAIL:
                response = await client.get(OPEN_ALEX_BASE_URL, params=params)
            else:
                response = await client.get(OPEN_ALEX_BASE_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": str(exc)}

    data = response.json()

    # return data
    # Instead of returning the data (25 full results are far too large), we'll return the meta information only.
    return {"meta": data.get("meta")}


@mcp.tool()
async def search_openalex(q: str):
    params = {"search": q, "per_page": 5}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPEN_ALEX_BASE_URL, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": str(exc)}

    # DEBUG
    print("Response:", response)
    data = response.json()

    relevant_data = []
    # Extract relevant information
    for result in data.get("results", []):
        relevant_data.append(await relevant_data_from_response(result))

    # DEBUG
    print("Relevant Data:", relevant_data)

    return {"query": q, "results": relevant_data}


@mcp.tool()
async def get_openalex_by_id(id: str):
    params = {"per_page": 5}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{OPEN_ALEX_BASE_URL}/{id}", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": str(exc)}

    data = response.json()

    data = await relevant_data_from_response(data)

    return {"id": id, "results": data}


async def relevant_data_from_response(data):
    # Extract relevant information from the OpenAlex API response

    # OpenAlex doesn't have the abstract because of legal reasons, so we'll fetch it from CrossRef if possible.
    if (
        data.get("indexed_in", []) and "crossref" in data.get("indexed_in", [])
    ) and data.get("ids", dict()).get("doi"):
        doi_as_url = data["ids"]["doi"]
        # This is in the format `https://doi.org/{doi}`
        doi = doi_as_url.split("https://doi.org/")[-1]
        abstract = await get_abstract_from_crossref(doi)
    else:
        abstract = None
    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "authors": [
            author.get("author", dict()).get("display_name", "")
            for author in data.get("authorships", [])
        ],
        "abstract": abstract if abstract else "",
        "published_date": data.get("published_date"),
        "fwci": data.get("fwci", -1),
        "open_access": data.get(
            "open_access", dict()
        ),  # This might help if the model wants to see the content as a PDF
        "cited_by_count": data.get("cited_by_count", -1),
        "primary_topic": data.get("primary_topic", dict()).get("display_name", ""),
        "subfield": data.get("primary_topic", dict())
        .get("subfield", dict())
        .get("display_name", ""),
        "pdf_url": data.get("best_oa_location", dict()).get("pdf_url", ""),
        # OpenAlex also has the concepts list, should we include that as well?
        # Same with referenced or related works.
    }


async def get_abstract_from_crossref(doi: str) -> str | None:
    """Fetch the abstract of a paper from CrossRef using its DOI."""
    CROSSREF_API_URL = f"https://api.crossref.org/works/{doi}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(CROSSREF_API_URL)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Error fetching abstract from CrossRef for DOI {doi}: {exc}")
            return None

    data = response.json()
    abstract = data.get("message", {}).get("abstract", "")
    return abstract if abstract else None


if __name__ == "__main__":
    print("Starting Literature Access service...", flush=True)
    # mcp.run(transport="streamable-http")
    import uvicorn

    uvicorn.run(mcp.streamable_http_app, host="0.0.0.0", port=8000)
else:
    print("DEBUG: Not running as main module.", flush=True)
