import streamlit as st
import os
import sys
import asyncio
import nest_asyncio
from typing import List
from datetime import datetime
import json
import io
import copy
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.chat_agent.graph import create_chat_graph, ChatAgentState
from app.utils.setup import setup
from app.utils.llm import clean_llm_response
from app.doc_handlers.pdf import parse_pdf_form, fill_pdf_form
from app.context.loader import load_file_into_context
from app.form.prefill import prefill_in_memory_form
from app.utils.misc import save_file_to_disk
from app.form.update import is_form_question, update_draft_form, get_prefilled_fields_status
from app.chat_agent.helpers import feedback_on_file_upload, feedback_on_support_docs_update

setup()

# Patches asyncio to allow nested event loops
nest_asyncio.apply()

DEFAULT_AI_GREETING = """
    Hello! 👋 I'm Form Pilot, your form assistant. Need to fill out a form? I'm here to help. Please start by uploading a form.
"""
SUPPORT_DOCS_PATH = os.path.join(os.getcwd(), os.getenv("SUPPORT_DOCS_PATH"))
FORMS_PATH = os.path.join(os.getcwd(), os.getenv("FORMS_PATH"))

# ---------- Streamlit Page Configuration ----------
st.set_page_config(page_title="Form Pilot", layout="wide")

# Custom CSS to change button colors
st.markdown("""
<style>
.stFileUploader button:hover,
.stDownloadButton button:hover,
.stButton > button:hover,
.stFileUploader button:active,
.stDownloadButton button:active,
.stButton > button:active {
    border-color: #c9a912;
    color: #f4c707;
}
.stFileUploader button:focus,
.stDownloadButton button:focus,
.stButton > button:focus {
    border-color: #c9a912 !important;
    color: #f4c707 !important;
    outline: 2px solid #c9a912 !important;
}
.stChatInput > div:focus-within {
    border-color: #f4c707 !important;
}
</style>
""", unsafe_allow_html=True)

def reset_session_state():
    """Clear all session state variables"""
    # TODO: Clear file uploaders too
    for key in list(st.session_state.keys()):
        del st.session_state[key]

async def on_support_docs_change():
    """Process support docs whenever the uploader changes"""   
    for doc in st.session_state.support_docs:
        if doc.name not in st.session_state.uploaded_doc_names and st.session_state.main_form_path:
            filepath = save_file_to_disk(doc, SUPPORT_DOCS_PATH)
            support_doc = await load_file_into_context(filepath)
            st.session_state.context_docs.append(support_doc)
            prefilled_form = await prefill_in_memory_form(st.session_state.draft_form, st.session_state.context_docs)
            st.session_state.draft_form = prefilled_form
            st.session_state.uploaded_doc_names.append(doc.name)
    
    # TODO: Handle the removal of support docs
    # For now, we're only addressing the addition of support docs, not the removal
    fields_changes = get_prefilled_fields_status(st.session_state.previous_draft_form, st.session_state.draft_form)    
    feedback = await feedback_on_support_docs_update(st.session_state.chat_graph, fields_changes)
    # Append it to the message history
    st.session_state.messages.extend(feedback)
    st.session_state.previous_draft_form = copy.deepcopy(st.session_state.draft_form)

# ---------- Initialize Session State ----------
if "main_form_path" not in st.session_state:
    st.session_state.main_form_path = None
if "support_docs" not in st.session_state:
    st.session_state.uploaded_doc_names = []
if "context_docs" not in st.session_state:
    st.session_state.context_docs = []
if "draft_form" not in st.session_state:
    st.session_state.previous_draft_form = None
    st.session_state.draft_form = None
if 'chat_graph' not in st.session_state:
    st.session_state.chat_graph = create_chat_graph()
    st.session_state.messages = [
        SystemMessage(content="You are a friendly and helpful assistant responsible for helping a user fill out a form."),
        AIMessage(content=DEFAULT_AI_GREETING)]

# ---------- Sidebar: File Uploads ----------
with st.sidebar:
    st.title("📂 Document Panel")

    st.subheader("Upload Form")
    main_form = st.file_uploader(
        "Upload the form document to be filled (PDF)",
        type=["pdf"],
        key="main_form_uploader",
    )
    if main_form and not st.session_state.main_form_path:
        st.session_state.main_form_path = save_file_to_disk(main_form, FORMS_PATH)
        # The initial draft form is just the parsed form (not prefilled)
        st.session_state.draft_form = parse_pdf_form(st.session_state.main_form_path)
        st.session_state.previous_draft_form = copy.deepcopy(st.session_state.draft_form)
        feedback = asyncio.run(feedback_on_file_upload(st.session_state.chat_graph, st.session_state.messages, st.session_state.draft_form))
        # Append it to the message history
        st.session_state.messages.extend(feedback)
        st.rerun()

    st.divider()

    st.subheader("Upload Support Documents")
    st.file_uploader(
        "Upload one or more support documents (PDF, DOCX, TXT, or Images)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="support_docs",
        on_change=lambda: asyncio.run(on_support_docs_change())
    )


# ---------- Main Section: Assistant Chat ----------
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.title("🧑‍🚀 Form Pilot", anchor=False)
    with col2:
        col_a, col_b, col_c = st.columns(3)
        
        with col_b:
            if st.session_state.draft_form:
                filled_pdf_bytes = fill_pdf_form(st.session_state.main_form_path, st.session_state.draft_form)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"form_{timestamp}.pdf"
            
                st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
                st.download_button(
                    label="⬇️ &nbsp;Download Form",
                    data=filled_pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    help="Download the filled form in PDF format",
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with col_c:
            st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
            if st.button("🔄 &nbsp;Start Over"):
                reset_session_state()
                st.rerun()  
            st.markdown("</div>", unsafe_allow_html=True)            


# Chat interface
chat_container = st.container(height=620)

# Display chat message history
with chat_container:
    for message in st.session_state.messages:
        if isinstance(message, SystemMessage) or isinstance(message, ToolMessage):
            continue
        elif isinstance(message, AIMessage) and not message.tool_calls:
            with st.chat_message("assistant"):
                st.write(clean_llm_response(message.content))
        elif isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to session state
    user_message = HumanMessage(content=prompt)

    previous_message = st.session_state.messages[-1]
    # Check if the user is submitting an answer to a form field
    is_user_responding_question = is_form_question(previous_message.content)
    if is_user_responding_question:
        # If the user is submitting an answer to a form field, we need to update the draft form
        st.session_state.draft_form = update_draft_form(st.session_state.draft_form, message.content)
    st.session_state.messages.append(user_message)

    # Display user message in chat history immediately
    with chat_container:
        with st.chat_message("user"):
            st.write(prompt)
    
    # Create agent state
    state = ChatAgentState(
        messages=st.session_state.messages, 
        draft_form=st.session_state.draft_form,
        form_filepath=st.session_state.main_form_path
    )
    
    # Process with the graph
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # With nest_asyncio, this should work even in nested loops
                result = asyncio.run(st.session_state.chat_graph.ainvoke(state))
            except Exception as e:
                st.error(f"Error processing request: {e}")
            
            # Update session state
            st.session_state.messages = result["messages"]
            st.rerun()
