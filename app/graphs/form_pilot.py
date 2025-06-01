from typing import Dict, List, TypedDict, Annotated, Union
import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
import PyPDF2

system_message = SystemMessage(
    content="""You are a helpful assistant that provides random information about a topic."""
)

# Define the state schema
class AgentState(TypedDict):
    messages: Annotated[List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]], add_messages]
    form_filepath: str
    form_data: Dict

# Factory function to create AgentState with system message
def create_agent_state(messages: List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]] = None, form_filepath: str = None) -> AgentState:
    all_messages = [system_message]
    if messages:
        all_messages.extend(messages)
    return AgentState(messages=all_messages, form_filepath=form_filepath)

def parse_pdf_form(state: AgentState) -> Dict:
    """
    Parse a PDF form and return the data as a dictionary in the required format.
    """
    form_filepath = state["form_filepath"]
    fields = []
    checkbox_groups = {}  # Dictionary to group checkboxes
    
    try:
        with open(os.path.join(os.getcwd(), form_filepath), "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if hasattr(reader, "get_fields") and callable(getattr(reader, "get_fields")):
                pdf_fields = reader.get_fields()
            else:
                pdf_fields = None
                
            if pdf_fields:
                # First pass: collect all checkboxes
                for field_name, field in pdf_fields.items():
                    field_type = field.get("/FT")
                    if field_type == "/Btn":
                        # Extract base name for checkbox group (remove any numeric suffix)
                        base_name = ''.join(c for c in field_name if not c.isdigit())
                        if base_name not in checkbox_groups:
                            checkbox_groups[base_name] = []
                        checkbox_groups[base_name].append({
                            "name": field_name,
                            "value": field.get("/V", "/Off"),
                            "description": field.get("/TU", "")
                        })
                    else:
                        # Handle non-checkbox fields
                        type_str = "dropdown" if field_type == "/Ch" else "text"
                        options = []
                        if type_str == "dropdown":
                            opts = field.get("/Opt")
                            if opts:
                                options = [str(opt) for opt in opts] if isinstance(opts, list) else [str(opts)]
                        
                        # Check if it's a list box (multiple selection dropdown)
                        if field.get("/Ff", 0) & 0x20000:  # 0x20000 is the flag for multiple selection
                            type_str = "list_box"
                        
                        fields.append({
                            "label": field_name,
                            "description": field.get("/TU", ""),
                            "type": type_str,
                            "docId": None,
                            "value": field.get("/V", ""),
                            "options": options,
                            "lastProcessed": "",
                            "lastSurveyed": ""
                        })
                
                # Second pass: add grouped checkboxes
                for base_name, checkboxes in checkbox_groups.items():
                    fields.append({
                        "label": base_name,
                        "description": checkboxes[0]["description"],
                        "type": "checkbox_group",
                        "docId": None,
                        "value": [cb["value"] for cb in checkboxes],
                        "options": [cb["name"] for cb in checkboxes],
                        "lastProcessed": "",
                        "lastSurveyed": ""
                    })
    except Exception as e:
        raise Exception(f"Error parsing PDF form: {str(e)}")
        
    return {
        "form_data": {
            "formFileName": form_filepath,
            "lastSaved": "",
            "fields": fields
        }
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
    workflow.add_node("parse_pdf_form", parse_pdf_form)
    
    workflow.set_entry_point("parse_pdf_form")
    
    return workflow.compile()
