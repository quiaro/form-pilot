from typing import Dict, List, TypedDict, Annotated, Union
import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
import PyPDF2

MAX_RETRIES = 3

# Define the state schema
class AgentState(TypedDict):
    form: Dict
    edited_form: Dict

def create_agent_state(form: Dict = None) -> AgentState:
    return AgentState(form=form)

def manage_form_completion(state: AgentState) -> Dict:
    """
    Manages the form completion with assistance from LLMs.
    """
    form = state["form"]
    edited_form = form.copy()
    unanswered_fields = []

    for field in filled_form["fields"]:
        if field["value"] == "":
            unanswered_fields.append(field)
        else:
            edited_form["fields"].append(field)
    
    for unanswered_field in unanswered_fields:
        while True:
            # TODO: Complete the implementation of the complete_form_field graph for this to work
            processed_field = complete_form_field(unanswered_field)
            if processed_field["valid"]:
                break
            else:
                if processed_field["retries"] >= MAX_RETRIES:
                    break
        
        field = {k: v for k, v in processed_field.items() if k not in ['retries', 'valid']}
        edited_form["fields"].append(field)
    
    # This is the final edited form after assisting the user. There may still be unanswered fields.
    return {"edited_form": edited_form}

# Build the graph
def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("manage_form_completion", manage_form_completion)
    workflow.set_entry_point("manage_form_completion")
    
    return workflow.compile()
