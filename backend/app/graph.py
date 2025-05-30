"""LangGraph implementation for trending information retrieval."""
from typing import Dict, List, TypedDict, Annotated, Sequence, Union, cast
import operator
import json
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from langchain_core.tools import BaseTool
from langchain_google_community.search import GoogleSearchRun, GoogleSearchAPIWrapper
from .tools import google_trends, reddit_search


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


# Factory function to create AgentState with system message
def create_agent_state(messages: List[Union[HumanMessage, AIMessage, SystemMessage, FunctionMessage]] = None) -> AgentState:
    all_messages = [system_message]
    if messages:
        all_messages.extend(messages)
    return AgentState(messages=all_messages)


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
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    model = model.bind_tools(tools)

    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent)
    workflow.add_node("tool_selector", tool_selector)
    
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue
    )
    workflow.add_edge("tool_selector", "agent")
    
    workflow.set_entry_point("agent")
    
    return workflow.compile()
