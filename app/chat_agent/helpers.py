from typing import Any, List
from langgraph.graph.graph import CompiledGraph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.chat_agent.graph import ChatAgentState
from app.models import DraftForm

async def trigger_chat_agent_response(agent_graph: CompiledGraph, messages: List[BaseMessage], human_message: str, **kwargs: Any) -> str:
    """
    Trigger the chat agent to respond to a human message.
    """
    user_message = HumanMessage(content=human_message)
    # Append user message to the messages list
    messages.append(user_message)
    state = ChatAgentState(messages=messages, **kwargs)
    result = await agent_graph.ainvoke(state)
    return result

async def feedback_on_file_upload(agent_graph: CompiledGraph, messages: List[BaseMessage], draft_form: DraftForm) -> List[AIMessage]:
    """
    Provide the user with feedback on the file they uploaded.
    Guide the user to next steps.
    """
    result = await trigger_chat_agent_response(
            agent_graph,
            [],
            "How many empty fields are there in the form?", 
            draft_form=draft_form
        )
    # Get the last message from the result
    empty_fields_response = result["messages"][-1]
    next_steps_response = AIMessage(content="Do you have any supporting documents related to the form?\nIf so, now would be a good time to upload them. I'll do my best to prefill the form with the information from the supporting documents.")
    
    return [empty_fields_response, next_steps_response]