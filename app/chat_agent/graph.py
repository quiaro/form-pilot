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

# State definition for the graph
@dataclass
class ChatAgentState:
    messages: List[BaseMessage]
    current_step: str = "process"

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

# Available tools
# tools = [get_current_time, calculate_math, word_count]
# tool_executor = ToolExecutor(tools)

# Simple response generation (in a real app, you'd use an LLM here)
def generate_response(state: ChatAgentState) -> Dict[str, Any]:
    last_message = state.messages[-1].content.lower()
    
    # Simple keyword-based responses (replace with actual LLM in production)
    if "time" in last_message or "date" in last_message:
        current_time = get_current_time.invoke({})
        response = f"The current time is: {current_time}"
    elif any(op in last_message for op in ['+', '-', '*', '/', 'calculate', 'math']):
        # Extract math expression (simplified)
        import re
        math_pattern = r'[\d+\-*/().\s]+'
        matches = re.findall(math_pattern, last_message)
        if matches:
            expression = matches[0].strip()
            response = calculate_math.invoke({"expression": expression})
        else:
            response = "Please provide a valid math expression to calculate."
    elif "count" in last_message and "word" in last_message:
        # Simple word count for the message itself
        response = word_count.invoke({"text": state.messages[-1].content})
    elif "hello" in last_message or "hi" in last_message:
        response = "Hello! I'm a simple chat agent built with LangGraph and Streamlit. I can help you with:\n- Getting current time\n- Simple math calculations\n- Word counting\n\nWhat would you like to do?"
    elif "help" in last_message:
        response = """I can help you with:
1. **Time**: Ask 'what time is it?' or 'current date'
2. **Math**: Ask me to calculate expressions like '5 + 3 * 2'
3. **Word Count**: Ask to 'count words in this text'
4. **General Chat**: Just say hello!

What would you like to try?"""
    else:
        response = "I'm a simple chat agent. I can help with time, math calculations, and word counting. Type 'help' for more information!"
    
    return {
        "messages": state.messages + [AIMessage(content=response)],
        "current_step": "complete"
    }

# Create the graph
def create_chat_graph():
    workflow = StateGraph(ChatAgentState)
    
    # Add nodes
    workflow.add_node("process", generate_response)
    
    # Set entry point
    workflow.set_entry_point("process")
    
    # Add edges
    workflow.add_edge("process", END)
    
    return workflow.compile()
