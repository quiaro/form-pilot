from typing import Dict, List, TypedDict, Annotated, Sequence, Union, cast
import operator
import json
import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from langchain_core.tools import BaseTool
from langchain_google_community.search import GoogleSearchRun, GoogleSearchAPIWrapper
from app.tools import google_trends, reddit_search
import PyPDF2


model = None

# Define the available tools
google_search_wrapper = GoogleSearchAPIWrapper(k=5)
google_search = GoogleSearchRun(api_wrapper=google_search_wrapper)
tools = [google_trends, google_search, reddit_search]

# Define the system message
system_message = SystemMessage(
    content="""You are a helpful assistant that provides random information about a topic.
    You have access to tools to provide this information. Use only the tools provided to return
    concise answers. Do not ask for feedback or offer to help with anything else."""
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
                    field_type = field.get("/FT", "text")
                    if field_type == "/Btn":
                        # Extract base name for checkbox group (remove any numeric suffix)
                        
                        # TODO: Get the correct labels for the checkboxes
                        base_name = ''.join(c for c in field_name if not c.isdigit())
                        if base_name not in checkbox_groups:
                            checkbox_groups[base_name] = []
                        checkbox_groups[base_name].append({
                            "name": field_name,
                            "value": field.get("/V", ""),
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
            else:
                # No AcroForm fields found
                pass
    except Exception as e:
        raise Exception(f"Error parsing PDF form: {str(e)}")
        
    return {
        "form_data": {
            "formFileName": form_filepath,
            "lastSaved": "",
            "fields": fields
        }
    }

# Define the agent node
def agent(state: AgentState) -> Dict:
    """
    Agent node that processes messages stored in the state.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with new messages returned from the tool selector node
    """
    messages = state["messages"]
    
    # Call OpenAI chat model
    response = model.invoke(messages)
    return {"messages": [response]}


# Define a conditional edge to check if we should continue
def should_continue(state: AgentState) -> str:
    """
    Determine if the agent should continue to tools or end.
    
    Args:
        state: Current state with messages
        
    Returns:
        Next node to route to
    """
    last_message = state["messages"][-1]
    
    # Check if the last message is a tool call
    if last_message.tool_calls:
        return "tool_selector"
    
    return END

# Create the tool selector node
tool_selector = ToolNode(tools=tools)

# Build the graph
def build_graph() -> StateGraph:
    """
    Build and return the LangGraph for trending information retrieval.
    
    Returns:
        A configured StateGraph
    """
    global model
    # model = ChatOpenAI(model="gpt-4o", temperature=0)
    # model = model.bind_tools(tools)

    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("parse_pdf_form", parse_pdf_form)
    # workflow.add_node("agent", agent)
    # workflow.add_node("tool_selector", tool_selector)
    
    # Add edges
    # workflow.add_conditional_edges(
    #     "agent",
    #     should_continue
    # )
    # workflow.add_edge("tool_selector", "agent")
    
    workflow.set_entry_point("parse_pdf_form")
    
    return workflow.compile()
