from typing import Dict, List, TypedDict, Annotated, Union, Any
import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from datetime import datetime

system_message = SystemMessage(
    content="""You are a precise form filling assistant that extracts information from documents to fill form fields accurately. 
    You carefully analyze the context and only provide information that is explicitly stated in the documents.
    If information is not found in the context, you leave the field empty."""
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

    print("\nStarting form filling process...")
    print(f"Number of documents loaded: {len(docs_data)}")
    print(f"Number of form fields to process: {len(form_data['fields'])}")

    form_fields = form_data["fields"]
    output_form = form_data.copy()
    output_fields = []
    # supporting documents
    context = "\n".join([doc_data_to_string(doc) for doc in docs_data])
    print(f"\nTotal context length: {len(context)} characters")
    print("First 200 characters of context:")
    print(context[:200] + "...")

    for field in form_fields:
        print(f"\nProcessing field: {field['label']} (Type: {field['type']})")
        output_field = field.copy()  # Always start with a copy

        try:
            if field["type"] == "text":
                print("Using text field processor...")
                output_field = await text_field_processor(field, context)
            elif field["type"] == "checkbox" or field["type"] == "checkbox_group":
                print("Using checkbox field processor...")
                output_field = await checkbox_field_processor(field, context)
            elif field["type"] == "dropdown":
                print("Using dropdown field processor...")
                output_field = await dropdown_field_processor(field, context)
            elif field["type"] == "list_box":
                print("Using list box field processor...")
                output_field = await list_box_field_processor(field, context)
            else:
                print(f"Warning: Unsupported field type: {field['type']} for field {field['label']}")
                output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"Field processed. Value: {output_field['value']}")
            if output_field.get("docId"):
                print(f"Information found in document: {output_field['docId']}")
            else:
                print("No matching information found in documents")
                
        except Exception as e:
            print(f"Error processing field {field['label']}: {str(e)}")
            output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_field["error"] = str(e)

        output_fields.append(output_field)

    output_form["fields"] = output_fields
    print("\nForm filling process completed.")
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

def format_pdf_value(value: Any, field_type: str, options: List[str] = None) -> Any:
    """
    Format a value according to PDF requirements.
    """
    if field_type == "checkbox_group":
        # For checkboxes, ensure we have a list of "/Yes" or "/Off" values
        if isinstance(value, list):
            return [str(v) if v in ["/Yes", "/Off"] else "/Off" for v in value]
        return ["/Off"]
    elif field_type == "dropdown" or field_type == "list_box":
        # For dropdowns and list boxes, ensure the value is in the options list
        if options and value not in options:
            return options[0] if field_type == "dropdown" else []
        return value
    else:
        # For text fields, convert to string
        return str(value) if value is not None else ""

def get_llm():
    """
    Get the LLM instance with proper configuration
    """
    # You need to replace this with your actual OpenAI API key
    OPENAI_API_KEY = ""  # Replace with your actual API key
    
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.0,
        api_key=OPENAI_API_KEY
    )

async def text_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a text field using the LLM.
    """
    try:
        # Extract information from context
        prompt = f"""Extract the {field['label']} from the following context. 
        If the information is not available, return an empty string.
        Context: {context}"""
        
        response = await get_llm().ainvoke(prompt)
        value = response.content.strip()
        
        return {
            "label": field["label"],
            "type": field["type"],
            "value": format_pdf_value(value, field["type"]),
            "options": field.get("options", [])
        }
    except Exception as e:
        return {
            "label": field["label"],
            "type": field["type"],
            "value": "",
            "options": field.get("options", [])
        }

async def checkbox_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a checkbox field using the LLM.
    """
    try:
        # Extract information from context
        prompt = f"""Determine if the {field['label']} should be checked based on the following context.
        Return a list of "/Yes" or "/Off" values for each checkbox in the group.
        Context: {context}"""
        
        response = await get_llm().ainvoke(prompt)
        value = response.content.strip()
        
        # Parse the response into a list of values
        values = [v.strip() for v in value.split(",")]
        values = [v if v in ["/Yes", "/Off"] else "/Off" for v in values]
        
        return {
            "label": field["label"],
            "type": field["type"],
            "value": format_pdf_value(values, field["type"]),
            "options": field.get("options", [])
        }
    except Exception as e:
        return {
            "label": field["label"],
            "type": field["type"],
            "value": ["/Off"] * len(field.get("options", [])),
            "options": field.get("options", [])
        }

async def dropdown_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a dropdown field using the LLM.
    """
    try:
        # Extract information from context
        prompt = f"""Select the most appropriate option for {field['label']} from the following options: {field['options']}
        Based on the context: {context}
        Return only the selected option."""
        
        response = await get_llm().ainvoke(prompt)
        value = response.content.strip()
        
        # Validate the response is in the options list
        if value not in field["options"]:
            value = field["options"][0]
        
        return {
            "label": field["label"],
            "type": field["type"],
            "value": format_pdf_value(value, field["type"], field["options"]),
            "options": field["options"]
        }
    except Exception as e:
        return {
            "label": field["label"],
            "type": field["type"],
            "value": field["options"][0] if field["options"] else "",
            "options": field["options"]
        }

async def list_box_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a list box field using the LLM.
    """
    try:
        # Extract information from context
        prompt = f"""Select all applicable options for {field['label']} from the following options: {field['options']}
        Based on the context: {context}
        Return a comma-separated list of selected options."""
        
        response = await get_llm().ainvoke(prompt)
        values = [v.strip() for v in response.content.split(",")]
        
        # Filter out invalid selections
        values = [v for v in values if v in field["options"]]
        
        return {
            "label": field["label"],
            "type": field["type"],
            "value": format_pdf_value(values, field["type"], field["options"]),
            "options": field["options"]
        }
    except Exception as e:
        return {
            "label": field["label"],
            "type": field["type"],
            "value": [],
            "options": field["options"]
        }

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
