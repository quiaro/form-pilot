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

@dataclass
class ChatAgentState:
    messages: Annotated[List[BaseMessage], operator.add]
    form_filepath: str = None

llm = None

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def chat_agent(state: ChatAgentState) -> Dict[str, Any]:
    messages = state.messages

    # Add system message with state context if needed
    context_message = SystemMessage(
        content=f"Current form filepath: {state.form_filepath or 'None'}"
    )
    messages_with_context = [context_message] + messages

    response = await llm.ainvoke(messages_with_context)
    return {"messages" : [response]}

tools = [get_current_time]
tool_node = ToolNode(tools=tools)

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
    
    # Set entry point
    workflow.set_entry_point("chat_agent")
    workflow.add_conditional_edges(
        "chat_agent",
        should_continue
    )
    workflow.add_edge("tools", "chat_agent")

    return workflow.compile()
