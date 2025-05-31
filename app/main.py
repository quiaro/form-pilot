import os
from app.utils.setup import setup

# Call setup to initialize environment
setup()

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import markdown
from langchain_core.messages import HumanMessage, AIMessage
from app.graphs.form_pilot import build_graph as build_form_pilot_graph, create_agent_state as form_pilot_create_agent_state
from app.graphs.load_context import build_graph as build_load_context_graph, create_agent_state as load_context_create_agent_state
from app.graphs.pre_fill_form import build_graph as build_pre_fill_form_graph, create_agent_state as pre_fill_form_create_agent_state
from datetime import datetime
from pydantic import BaseModel


form_pilot_graph = build_form_pilot_graph()
load_context_graph = build_load_context_graph()
pre_fill_form_graph = build_pre_fill_form_graph()
app = FastAPI(title="Form Pilot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Valid categories
VALID_CATEGORIES = [
    "Business and Finance",
    "Entertainment",
    "Food and Drink",
    "Games",
    "Health",
    "Hobbies and Leisure",
    "Jobs and Education",
    "Science",
    "Sports",
    "Technology"
]

class ParsePDFFormRequest(BaseModel):
    pdf_file: str

@app.post("/api/parse_pdf_form")
async def parse_pdf_form(request: ParsePDFFormRequest):
    """
    Parse a PDF form given its file path.
    """
    # Get the form filepath from the request
    form_filepath = request.pdf_file

    state = form_pilot_create_agent_state(form_filepath=form_filepath)
    output = await form_pilot_graph.ainvoke(state)
    return output["form_data"]


class LoadContextRequest(BaseModel):
    document_filepaths: List[str]

@app.post("/api/load_context")
async def load_context(request: LoadContextRequest):
    """
    Load context from a list of document file paths.
    """
    # Get the form filepath from the request
    docs_filepaths = request.document_filepaths

    state = load_context_create_agent_state(docs_filepaths=docs_filepaths)
    output = await load_context_graph.ainvoke(state)
    return output["docs_data"]


class PreFillFormRequest(BaseModel):
    form_data: Dict
    docs_data: List[Dict]

@app.post("/api/pre_fill_form")
async def pre_fill_form(request: PreFillFormRequest):
    """
    Pre-fill a form with context from a list of document file paths.
    """
    # Get the form filepath from the request
    form_data = request.form_data
    docs_data = request.docs_data

    state = pre_fill_form_create_agent_state(form_data=form_data, docs_data=docs_data)
    output = await pre_fill_form_graph.ainvoke(state)
    return output["filled_form"]


@app.get("/api/categories")
async def get_categories():
    """
    Get the list of valid categories.
    
    Returns:
        List of valid categories
    """
    return {"categories": VALID_CATEGORIES}

# Determine the frontend build directory 
# If in Docker, the frontend build is at /app/frontend/build
# If running locally, use relative path ../frontend/build
FRONTEND_BUILD_DIR = "/app/frontend/build"
FRONTEND_STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "assets")
FRONTEND_INDEX_HTML = os.path.join(FRONTEND_BUILD_DIR, "index.html")

# Mount the frontend build folder (only in production)
if os.getenv("ENV", "development").lower() == "production":
    print("Production environment detected")
    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(FRONTEND_INDEX_HTML)

    # Catch-all route to serve React Router paths
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        # If the path is an API endpoint, skip this handler
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check if a static file exists in the build folder
        static_file_path = os.path.join(FRONTEND_BUILD_DIR, full_path)
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        # Otherwise, serve the index.html for client-side routing
        return FileResponse(FRONTEND_INDEX_HTML)

    # Mount static files (JavaScript, CSS, images)
    app.mount("/assets", StaticFiles(directory=FRONTEND_STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    env = os.getenv("ENV", "development")
    
    # Only enable auto-reload in development
    reload = env.lower() == "development"
    
    uvicorn.run("app.main:app", host=host, port=port, reload=reload) 