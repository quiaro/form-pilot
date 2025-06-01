from typing import Dict, List, TypedDict, Annotated, Union
import os
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage
from app.utils.llm import clean_llm_response

general_system_message = """You are a helpful assistant that wants to help the user answer a field in a form. 
    You will be given information about the form field and your goal is to come up with a question that will solicit the information needed to answer the field.
    """

# Define the state schema
class AgentState(TypedDict):
    form_fields: List[Dict]
    unanswered_field: Dict
    question: str

# Factory function to create AgentState with system message
def create_agent_state(form_fields: List[Dict] = None, unanswered_field: Dict = None) -> AgentState:
    return AgentState(form_fields=form_fields, unanswered_field=unanswered_field)

async def field_surveyor(state: AgentState):
    """
    Given a form field, the goal is to come up with a question that will solicit the information needed to answer the field.
    The question has to take into account the field type and the context of the form.
    """
    form_fields = state["form_fields"]
    unanswered_field = state["unanswered_field"]

    if unanswered_field["type"] == "text":
        return await text_field_surveyor(state)
    elif unanswered_field["type"] == "checkbox_group":
        return checkbox_field_surveyor(state)
    elif unanswered_field["type"] == "dropdown":
        return dropdown_field_surveyor(state)
    else:
        raise ValueError(f"Unsupported field type: {unanswered_field['type']}")

async def text_field_surveyor(state: AgentState):
    """
    Given a text field, the goal is to come up with a question that will solicit the information needed to answer the field.
    """
    form_fields = state["form_fields"]
    unanswered_field = state["unanswered_field"]

    PROMPT = f"""
    {general_system_message}

    As context, take into account all the fields in the form:
    <form>
        {form_fields}
    </form>
    
    The field that the user needs to answer is:
    <field>
        <label>{unanswered_field["label"]}</label>
        <description>{unanswered_field["description"]}</description>
        <type>{unanswered_field["type"]}</type>
    </field>

    Ask a polite and clear question that will help the user answer the field. /no_think
    """

    model = ChatOllama(model=os.getenv("QUESTIONS_LLM"), temperature=0.2)
    response = await model.ainvoke(PROMPT)
    question = clean_llm_response(response.content)
    return {"question": question}

def checkbox_field_surveyor(state: AgentState):
    """
    Given a checkbox field, the goal is to come up with a question that will solicit the information needed to answer the field.
    """
    # TODO: Implement checkbox field surveyor
    return "What is the checkbox field's answer?"

def dropdown_field_surveyor(state: AgentState):
    """
    Given a dropdown field, the goal is to come up with a question that will solicit the information needed to answer the field.
    """
    # TODO: Implement dropdown field surveyor
    return "What is the dropdown field's answer?"


# Build the graph
def build_graph() -> StateGraph:    
    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("field_surveyor", field_surveyor)    
    workflow.set_entry_point("field_surveyor")    
    return workflow.compile()
