from typing import Dict, List, TypedDict, Annotated, Union
import os
import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from datetime import datetime

system_message = SystemMessage(
    content="""You are a helpful assistant that provides random information about a topic."""
)

# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]], add_messages]
    form_data: Dict
    docs_data: List[Dict]
    filled_form: Dict

# Factory function to create AgentState with system message
def create_agent_state(messages: List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]] = None, form_data: Dict = None, docs_data: List[Dict] = None) -> AgentState:
    all_messages = [system_message]
    if messages:
        all_messages.extend(messages)
    return AgentState(messages=all_messages, form_data=form_data, docs_data=docs_data)

def doc_data_to_string(doc_data: Dict) -> str:
    """
    Convert a document data dictionary to a string

    Returns:
        A string of the form:
        <reference_start>
           Document ID: {doc_data['docId']}
           Content: {doc_data['content']}
        <reference_end>
    """
    return f"""
    <reference>
        <document_id>
            {doc_data['docId']}
        </document_id>
        <content>
            {doc_data['content']}
        </content>
    </reference>
    """

async def in_memory_form_filler(state: AgentState) -> Dict:
    """
    Loops through all form fields and calls the corresponding field processor for each field.

    Args:
        state: The current state of the agent

    Returns:
        A dictionary with the updated form data
    """
    form_data = state["form_data"]
    docs_data = state["docs_data"]

    form_fields = form_data["fields"]
    output_form = form_data.copy()
    output_fields = []
    # supporting documents
    context = "\n".join([doc_data_to_string(doc) for doc in docs_data])

    for field in form_fields:
        output_field = field.copy()  # Always start with a copy

        try:
            if field["type"] == "text":
                output_field = await text_field_processor(field, context)
            elif field["type"] == "checkbox":
                output_field = checkbox_field_processor(field, context)
            elif field["type"] == "dropdown":
                output_field = dropdown_field_processor(field, context)
            else:
                raise ValueError(f"Unsupported field type: {field['type']}")
        except Exception as e:
            output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_field["error"] = str(e)

        output_fields.append(output_field)

    output_form["fields"] = output_fields
    return {"filled_form": output_form}

def parse_llm_response(response):
    try:
        data = json.loads(response.strip())
        # Ensure required keys exist with defaults
        return {
            "value": data.get("value", ""),
            "docId": data.get("docId")
        }
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}")

async def text_field_processor(field: Dict, context: str) -> Dict:
    """
    Uses an LLM to find the answer to the field using the context data. If the context data is not enough for filling the field, leave the field empty.
    """
    llm = ChatOllama(
        model="gemma3:4b",
        temperature=0.0
    )

    PROMPT = """
        You are a helpful assistant whose task is to answer a field in a form to the best of your ability.
        You are given information about the field and context to answer. 
        You can only use the context to answer the field.

        Respond with valid JSON only. Do not wrap in code blocks or add explanatory text.

        Examples of correct responses:
        {{"value": "John Smith", "docId": "doc123"}}
        {{"value": "", "docId": null}}

        Rules:
        - If context lacks information: {{"value": "", "docId": null}}
        - If context has information: {{"value": "your_answer", "docId": "source_document_id"}}
        - Use null (not None) for missing docId
        - Keep answers succinct

        Field information: 
        - Label: {field[label]}
        - Description: {field[description]}
        - Type: {field[type]}

        Context: {context}
    """
    rag_prompt = ChatPromptTemplate.from_template(PROMPT)
    messages = rag_prompt.format_messages(field=field, context=context)

    response = await llm.ainvoke(messages)
    output_field = field.copy()
    parsed_response = parse_llm_response(response.content)
    output_field["value"] = parsed_response["value"]
    output_field["docId"] = parsed_response["docId"]
    output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return output_field


def checkbox_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a checkbox field
    """
    # TODO: Implement checkbox field processor
    output_field = field.copy()
    return output_field


def dropdown_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a dropdown field
    """
    # TODO: Implement checkbox field processor
    output_field = field.copy()
    return output_field

def create_form_checkpoint(state: AgentState) -> Dict:
    """
    Persist in-memory data structure of the form to disk
    """
    filled_form = state["filled_form"]
    filled_form["lastSaved"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = filled_form["formFileName"]
    filename = filename.replace("/forms/", "/checkpoints/")
    filename = filename.replace(".pdf", ".json")
    with open(filename, "w") as f:
        json.dump(filled_form, f)
    return state

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
    workflow.add_node("in_memory_form_filler", in_memory_form_filler)
    workflow.add_node("create_form_checkpoint", create_form_checkpoint)
    
    workflow.set_entry_point("in_memory_form_filler")
    workflow.add_edge("in_memory_form_filler", "create_form_checkpoint")
    workflow.add_edge("create_form_checkpoint", END)

    return workflow.compile()
