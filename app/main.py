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
from app.graphs.complete_form_field import build_graph as build_complete_form_field_graph, create_agent_state as complete_form_field_create_agent_state
from app.graphs.judge_answer import build_graph as build_judge_answer_graph, create_agent_state as judge_answer_create_agent_state
from datetime import datetime
from pydantic import BaseModel


form_pilot_graph = build_form_pilot_graph()
load_context_graph = build_load_context_graph()
pre_fill_form_graph = build_pre_fill_form_graph()
complete_form_field_graph = build_complete_form_field_graph()
judge_answer_graph = build_judge_answer_graph()
app = FastAPI(title="Form Pilot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class GenerateQuestionRequest(BaseModel):
    form_data: Dict
    unanswered_field: Dict

@app.post("/api/complete_form_field")
async def complete_form_field(request: GenerateQuestionRequest):
    """
    Generate a question for a form field.
    """
    form_fields = request.form_data["fields"]
    form_field = request.unanswered_field

    state = complete_form_field_create_agent_state(form_fields=form_fields, unanswered_field=form_field)
    output = await complete_form_field_graph.ainvoke(state)
    return output["question"]

class JudgeAnswerRequest(BaseModel):
    form_data: Dict
    unanswered_field: Dict
    answer: str

@app.post("/api/judge_answer")
async def judge_answer(request: JudgeAnswerRequest):
    """
    Generate a question for a form field.
    """
    form_fields = request.form_data["fields"]
    unanswered_field = request.unanswered_field
    answer = request.answer

    state = judge_answer_create_agent_state(form_fields=form_fields, unanswered_field=unanswered_field, answer=answer)
    output = await judge_answer_graph.ainvoke(state)
    return output["answered_field"]

if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_TEST_HOST", "0.0.0.0")
    port = int(os.getenv("API_TEST_PORT", "8000"))
    env = os.getenv("ENV", "development")
    
    # Only enable auto-reload in development
    reload = env.lower() == "development"
    
    uvicorn.run("app.main:app", host=host, port=port, reload=reload) 