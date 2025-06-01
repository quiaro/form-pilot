from typing import Dict, List, TypedDict, Annotated, Union
import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from datetime import datetime
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
import PyPDF2

system_message = SystemMessage(
    content="""You are a precise document processing assistant that extracts and structures information from documents.
    You carefully analyze the content and maintain the original meaning and context."""
)

# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]], add_messages]
    docs_filepaths: List[str]
    docs_data: List[Dict]

# Factory function to create AgentState with system message
def create_agent_state(messages: List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]] = None, docs_filepaths: List[str] = None) -> AgentState:
    all_messages = [system_message]
    if messages:
        all_messages.extend(messages)
    return AgentState(messages=all_messages, docs_filepaths=docs_filepaths)

async def context_manager(state: AgentState) -> Dict:
    """
    Load the contents of all supporting documents into a data structure in memory
    """
    docs_filepaths = state["docs_filepaths"]
    docs_data = []
    
    print(f"\nLoading {len(docs_filepaths)} documents...")
    
    for filepath in docs_filepaths:
        print(f"\nProcessing document: {filepath}")
        try:
            if filepath.endswith(".docx"):
                print("Loading Word document...")
                doc_data = document_loader_word_document(filepath)
            elif filepath.endswith(".pdf"):
                print("Loading PDF document...")
                doc_data = document_loader_pdf(filepath)
            elif filepath.endswith(".txt"):
                print("Loading text document...")
                doc_data = document_loader_text(filepath)
            else:
                print(f"Warning: Unsupported file type: {filepath}")
                continue
                
            if doc_data and doc_data.get("content"):
                print(f"Successfully loaded document. Content length: {len(doc_data['content'])} characters")
                print("First 200 characters of content:")
                print(doc_data['content'][:200] + "...")
                docs_data.append(doc_data)
            else:
                print(f"Warning: No content extracted from {filepath}")
                
        except Exception as e:
            print(f"Error loading document {filepath}: {str(e)}")
            docs_data.append({
                "docId": filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "docType": "error",
                "dateCreated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content": f"Error loading document: {str(e)}"
            })

    if not docs_data:
        raise ValueError("No valid documents were loaded")

    total_length = sum(len(doc["content"]) for doc in docs_data)
    print(f"\nTotal content length across all documents: {total_length} characters")
    
    if total_length > 204800:
        print(f"Warning: Total document length ({total_length}) exceeds recommended limit (204800)")
    
    return {"docs_data": docs_data}

def document_loader_word_document(filepath: str) -> str:
    """
    Load a Word document into a doc dictionary

    Returns:
        A dictionary with the following keys:
        - "docId": filepath + timestamp
        - "docType": "word"
        - "dateCreated": timestamp
        - "content": The text of the document
    """
    doc_id = filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S")
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    docs = list(UnstructuredWordDocumentLoader(filepath, mode="single").lazy_load())
    content = "".join([doc.page_content for doc in docs])
    return {
        "docId": doc_id,
        "docType": "docx",
        "dateCreated": date_created,  
        "content": content
    }

def document_loader_pdf(filepath: str) -> Dict:
    """
    Load a PDF document into a doc dictionary
    """
    doc_id = filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S")
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
                
        return {
            "docId": doc_id,
            "docType": "pdf",
            "dateCreated": date_created,
            "content": content.strip()
        }
    except Exception as e:
        raise Exception(f"Error loading PDF: {str(e)}")

def document_loader_text(filepath: str) -> Dict:
    """
    Load a text file into a doc dictionary
    """
    doc_id = filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S")
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "docId": doc_id,
            "docType": "text",
            "dateCreated": date_created,
            "content": content.strip()
        }
    except Exception as e:
        raise Exception(f"Error loading text file: {str(e)}")

# Build the graph
def build_graph() -> StateGraph:
    """
    Build and return the LangGraph for trending information retrieval.
    
    Returns:
        A configured StateGraph
    """
    global model

    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("context_manager", context_manager)
    
    workflow.set_entry_point("context_manager")
    
    return workflow.compile()
