from typing import List, Annotated
import operator
import streamlit as st
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
from langchain_core.messages.base import BaseMessage
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
import json
from app.utils.llm import get_llm
from langgraph.prebuilt import ToolNode
from app.models import DraftForm
from app.form.inquire import field_surveyor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser

@dataclass
class ChatAgentState:
    messages: Annotated[List[BaseMessage], operator.add]
    form_filepath: str = None
    draft_form: DraftForm = None
    next: str = None  # For storing supervisor routing decisions

llm = None

def create_supervisor(llm, system_prompt, members, members_descriptions) -> str:
    """An LLM-based router."""
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": members},
                    ],
                },
            },
            "required": ["next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "{members_descriptions}. Given the conversation above, who should act next? Select one of: {members}."
            ),
        ]
    ).partial(members=str(members), members_descriptions=str(members_descriptions))
    
    async def supervisor_chain(state: ChatAgentState):
        # Extract messages from state and pass to prompt
        result = await (
            prompt
            | llm.bind_functions(functions=[function_def], function_call="route")
            | JsonOutputFunctionsParser()
        ).ainvoke({"messages": state.messages})
        return result
    
    return supervisor_chain


async def workflow_guide_node(state: ChatAgentState) -> Dict[str, Any]:
    messages = state.messages

    system_prompt = """
    You are a friendly and cheerful assistant whose goal is to guide the user through a workflow.
    If the user is not familiar with the workflow, guide them through it.

    The workflow is as follows:    
    1. User uploads the form that needs to be completed
    2. User uploads any support documents relevant to the form.
    3. User fills out any remaining empty fields in the form.

    You help the user stay focused on the workflow.
    /no_think
    """

    if state.form_filepath:
        upload_message = "Form upload check: form uploaded."
    else:
        upload_message = "Form upload check: no form uploaded."
    extended_messages = messages + [SystemMessage(content=system_prompt)] + [AIMessage(content=upload_message)]

    response = await llm.ainvoke(extended_messages)
    return {"messages" : [response]}


async def form_completion_node(state: ChatAgentState) -> Dict[str, Any]:
    draft_form = state.draft_form
    unanswered_fields = []

    for field in draft_form["fields"]:
        if field["value"] == "":
            unanswered_fields.append(field)

    if len(unanswered_fields) > 0:
        unanswered_field = unanswered_fields[0]
        question = await field_surveyor(draft_form["fields"], unanswered_field)
        return {"messages" : [AIMessage(content=f"[{len(unanswered_fields)} fields left] {question}")]}
    else:
        return {"messages" : [AIMessage(content="All fields have been answered. Feel free to download the form or start filling in a new one. Thank you for using Form Pilot!")]}


async def supervisor_node(state: ChatAgentState) -> Dict[str, Any]:
    """Wrapper node for the supervisor to handle state properly"""
    global llm
    supervisor_agent = create_supervisor(llm, 
        "You are a supervisor responsible for helping a user fill out a form. You must decide which worker needs to act next.",
        ["WorkflowGuide", "FormCompletionAssistant"],
        ("WorkflowGuide explains the workflow to the user and prompts them to upload a form. "
         "FormCompletionAssistant helps the user fill out the form after it has been uploaded.")
    )
    
    result = await supervisor_agent(state)
    return {"next": result["next"]}
    
# Create the graph
def create_chat_graph():
    global llm
    llm = get_llm(type="CHAT_LLM", temperature=0.2)
    
    workflow = StateGraph(ChatAgentState)
    
    # Add nodes
    workflow.add_node("WorkflowGuide", workflow_guide_node)
    workflow.add_node("FormCompletionAssistant", form_completion_node)
    workflow.add_node("Supervisor", supervisor_node)
    
    # Connect nodes
    workflow.add_conditional_edges(
        "Supervisor",
        lambda state: state.next,
        {"WorkflowGuide": "WorkflowGuide", "FormCompletionAssistant": "FormCompletionAssistant"}
    )
    workflow.add_edge("WorkflowGuide", END)
    workflow.add_edge("FormCompletionAssistant", END)
    
    # Set entry point
    workflow.set_entry_point("Supervisor")    

    return workflow.compile()
