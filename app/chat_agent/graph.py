from typing import List, Annotated
import operator
import streamlit as st
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor
from langchain_core.messages.base import BaseMessage
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
import json
import datetime
from app.utils.llm import get_llm
from langgraph.prebuilt import ToolNode
from app.models import DraftForm
from app.form.inquire import field_surveyor

@dataclass
class ChatAgentState:
    messages: Annotated[List[BaseMessage], operator.add]
    form_filepath: str = None
    draft_form: DraftForm = None

llm = None

@tool
def fill_form() -> str:
    """Fill the form."""
    # HACK: Best way yet to route to the form completion node
    # from the initial chat agent. Perhaps this could be 
    # replaced with a router LLM that decides where to route 
    # (chat agent, form completion node or other nodes)
    return "Proceed to fill the form"

async def chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    messages = state.messages

    # Add system message with state context if needed
    context_message = SystemMessage(
        content=f"Current form filepath: {state.form_filepath or 'None'}"
    )
    messages_with_context = [context_message] + messages

    response = await llm.ainvoke(messages_with_context)
    return {"messages" : [response]}

tools = [fill_form]
tool_node = ToolNode(tools=tools)

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

def should_continue(state):
    last_message = state.messages[-1]

    if last_message.tool_calls:
        return "tools"

    return END
    
# Create the graph
def create_chat_graph():
    global llm
    # base_llm = get_chat_llm(model="gpt-4o-mini", temperature=0.2)
    base_llm = get_llm(type="CHAT_LLM", temperature=0.2)
    llm = base_llm.bind_tools(tools)  # Now LLM knows about the tools!

    workflow = StateGraph(ChatAgentState)
    
    # Add nodes
    workflow.add_node("chat_agent", chat_agent)
    workflow.add_node("tools", tool_node)
    workflow.add_node("form_completion_node", form_completion_node)
    
    # Set entry point
    workflow.set_entry_point("chat_agent")
    workflow.add_conditional_edges(
        "chat_agent",
        should_continue
    )
    workflow.add_edge("tools", "form_completion_node")
    workflow.add_edge("form_completion_node", END)

    return workflow.compile()
