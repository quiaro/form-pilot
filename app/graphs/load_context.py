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
    content="""You are a helpful assistant that provides random information about a topic."""
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
    for filepath in docs_filepaths:

        # TODO: Add support for other file types
        try:
            if filepath.endswith(".docx"):
                doc_data = document_loader_word_document(filepath)
                docs_data.append(doc_data)
            else:
                raise ValueError(f"Unsupported file type: {filepath}")
        except Exception as e:
            # Add error information to docs_data
            docs_data.append({
                "docId": filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "docType": "error",
                "dateCreated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content": f"Error loading document: {str(e)}"
            })

    total_length = sum(len(doc["content"]) for doc in docs_data)
    # Assuming the max context length is 128k, we'll only use 40% of that 
    # (~51,200 tokens ... ~204,800 characters) for the supporting documents
    if total_length > 204800:
        raise ValueError("Max support documents exceeded")
    
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
