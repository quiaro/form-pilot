from typing import List, Annotated
import operator
import streamlit as st
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor
from langchain_core.messages.base import BaseMessage
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
import json
import datetime
from app.utils.llm import get_llm

@dataclass
class ChatAgentState:
    messages: Annotated[List[BaseMessage], operator.add]
    current_step: str = "process"

llm = None

# Sample tools for the agent
@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculate_math(expression: str) -> str:
    """Calculate a simple math expression safely."""
    try:
        # Only allow basic math operations for safety
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "Error: Only basic math operations are allowed"
        
        result = eval(expression)
        return f"The result is: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"

@tool
def word_count(text: str) -> str:
    """Count words in the given text."""
    word_count = len(text.split())
    char_count = len(text)
    return f"Word count: {word_count}, Character count: {char_count}"


async def generate_response(state: ChatAgentState) -> Dict[str, Any]:
    messages = state.messages
    response = await llm.ainvoke(messages)
    return {"messages" : [response]}

def should_continue(state):
    last_message = state.messages[-1]

    if last_message.content.lower() == "continue":
        return "process"

    return END
    
# Create the graph
def create_chat_graph():
    global llm
    llm = get_llm("CHAT_LLM")

    workflow = StateGraph(ChatAgentState)
    
    # Add nodes
    workflow.add_node("process", generate_response)
    workflow.add_conditional_edges(
        "process",
        should_continue
    )
    
    # Set entry point
    workflow.set_entry_point("process")
    
    return workflow.compile()
