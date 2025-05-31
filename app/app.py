import streamlit as st
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import markdown
from langchain_core.messages import HumanMessage, AIMessage
from app.graphs.form_pilot import build_graph as build_form_pilot_graph, create_agent_state as form_pilot_create_agent_state
from app.graphs.load_context import build_graph as build_load_context_graph, create_agent_state as load_context_create_agent_state
from app.graphs.pre_fill_form import build_graph as build_pre_fill_form_graph, create_agent_state as pre_fill_form_create_agent_state
from datetime import datetime
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(title="Form Pilot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graphs
form_pilot_graph = build_form_pilot_graph()
load_context_graph = build_load_context_graph()
pre_fill_form_graph = build_pre_fill_form_graph()

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

# FastAPI Models
class ParsePDFFormRequest(BaseModel):
    pdf_file: str

class LoadContextRequest(BaseModel):
    document_filepaths: List[str]

class PreFillFormRequest(BaseModel):
    form_data: Dict
    docs_data: List[Dict]

# FastAPI Routes
@app.post("/api/parse_pdf_form")
async def parse_pdf_form(request: ParsePDFFormRequest):
    """
    Parse a PDF form given its file path.
    """
    form_filepath = request.pdf_file
    state = form_pilot_create_agent_state(form_filepath=form_filepath)
    output = await form_pilot_graph.ainvoke(state)
    return output["form_data"]

@app.post("/api/load_context")
async def load_context(request: LoadContextRequest):
    """
    Load context from a list of document file paths.
    """
    docs_filepaths = request.document_filepaths
    state = load_context_create_agent_state(docs_filepaths=docs_filepaths)
    output = await load_context_graph.ainvoke(state)
    return output["docs_data"]

@app.post("/api/pre_fill_form")
async def pre_fill_form(request: PreFillFormRequest):
    """
    Pre-fill a form with context from a list of document file paths.
    """
    form_data = request.form_data
    docs_data = request.docs_data
    state = pre_fill_form_create_agent_state(form_data=form_data, docs_data=docs_data)
    output = await pre_fill_form_graph.ainvoke(state)
    return output["filled_form"]

@app.get("/api/categories")
async def get_categories():
    """
    Get the list of valid categories.
    """
    return {"categories": VALID_CATEGORIES}

# Frontend build configuration
FRONTEND_BUILD_DIR = "/app/frontend/build"
FRONTEND_STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "assets")
FRONTEND_INDEX_HTML = os.path.join(FRONTEND_BUILD_DIR, "index.html")

# Mount frontend in production
if os.getenv("ENV", "development").lower() == "production":
    print("Production environment detected")
    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(FRONTEND_INDEX_HTML)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        static_file_path = os.path.join(FRONTEND_BUILD_DIR, full_path)
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
        
        return FileResponse(FRONTEND_INDEX_HTML)

    app.mount("/assets", StaticFiles(directory=FRONTEND_STATIC_DIR), name="static")

# Streamlit Interface
st.set_page_config(page_title="AI Document Assistant", layout="wide")

# ------------------ Session Initialization ------------------ #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "reset" not in st.session_state:
    st.session_state.reset = False

# ------------------ Sidebar: File Upload Sections ------------------ #
with st.sidebar:
    st.title("📂 Document Panel")

    st.subheader("1️⃣ Upload Main Form")
    main_form = st.file_uploader(
        "Upload the main document (PDF, DOCX, TXT, or Image)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="main_form"
    )

    if main_form:
        st.markdown("**✅ Main form uploaded:**")
        st.code(main_form.name)

    st.divider()

    st.subheader("2️⃣ Upload Support Documents")
    support_docs = st.file_uploader(
        "Upload one or more support documents (PDF, DOCX, TXT, or Images)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="support_docs"
    )

    if support_docs:
        st.markdown("**📎 Support documents uploaded:**")
        for idx, doc in enumerate(support_docs, 1):
            st.markdown(f"{idx}. `{doc.name}`")

    # Show Start Over if both uploads exist
    if main_form and support_docs:
        if st.button("🔄 Start Over"):
            # Clear session variables
            for key in ["main_form", "support_docs", "chat_history"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()

# ------------------ Main Area: Chat Interface ------------------ #
st.title("🧠 Form Assistant Chat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if main_form and support_docs:
    user_question = st.text_input("Ask a question about the documents:", key="user_question")

    if st.button("Submit"):
        if user_question.strip():
            st.session_state.chat_history.append(("user", user_question))
            # Placeholder response
            agent_response = "🤖 (This is a placeholder for the AI response.)"
            st.session_state.chat_history.append(("assistant", agent_response))
        else:
            st.warning("Please enter a question before submitting.")

    # Display chat history
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"**You:** {message}")
        else:
            st.markdown(f"**AI Assistant:** {message}")
else:
    st.info("👈 Please upload a main form and at least one support document to start asking questions.")

if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    env = os.getenv("ENV", "development")
    
    # Only enable auto-reload in development
    reload = env.lower() == "development"
    
    uvicorn.run("app.app:app", host=host, port=port, reload=reload)
