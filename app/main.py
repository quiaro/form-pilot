import streamlit as st
import os
import sys
import asyncio
import nest_asyncio
from typing import List
from datetime import datetime
import json
import io
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from app.chat_agent.prompts import SYSTEM_PROMPT, DEFAULT_AI_GREETING
from app.chat_agent.graph import create_chat_graph, ChatAgentState
from app.utils.setup import setup
from app.utils.llm import clean_llm_response
from app.doc_handlers.pdf import parse_pdf_form, fill_pdf_form
from app.context.loader import context_loader
from app.form.prefill import prefill_in_memory_form

setup()

# Patches asyncio to allow nested event loops
nest_asyncio.apply()

# ---------- Streamlit Page Configuration ----------
st.set_page_config(page_title="AI Document Assistant", layout="wide")

# ---------- Helper: Save Uploaded Files ----------
def save_uploaded_file(uploaded_file, folder="uploaded_docs"):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, uploaded_file.name)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.read())
    return filepath

# ---------- Session State ----------
if "main_form_path" not in st.session_state:
    st.session_state.main_form_path = None
if "support_doc_paths" not in st.session_state:
    st.session_state.support_doc_paths = []
if "form_draft" not in st.session_state:
    st.session_state.form_draft = None

# ---------- Sidebar: File Uploads ----------
with st.sidebar:
    st.title("📂 Document Panel")

    st.subheader("Upload Form")
    main_form = st.file_uploader(
        "Upload the form document to be filled (PDF)",
        type=["pdf"],
        key="main_form_uploader"
    )
    if main_form:
        st.session_state.main_form_path = save_uploaded_file(main_form)
        st.markdown(f"**✅ Uploaded:** `{main_form.name}`")

    st.divider()

    st.subheader("Upload Support Documents")
    support_docs = st.file_uploader(
        "Upload one or more support documents (PDF, DOCX, TXT, or Images)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="support_docs_uploader"
    )
    if support_docs:
        st.session_state.support_doc_paths = [save_uploaded_file(doc) for doc in support_docs]
        st.markdown("**📎 Support documents uploaded:**")
        for idx, doc in enumerate(support_docs, 1):
            st.markdown(f"{idx}. `{doc.name}`")

    if st.session_state.main_form_path and st.session_state.support_doc_paths:
        if st.button("🔄 Start Over"):
            for key in ["main_form_path", "support_doc_paths", "form_draft"]:
                st.session_state[key] = None if "path" in key else []
            st.rerun()


# ---------- Main Section: Assistant Chat ----------
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.title("🧑‍🚀 Form Pilot", anchor=False)
    with col2:
        col_a, col_b, col_c = st.columns(3)
        
        with col_b:
            st.markdown("""
                <style>
                    div[data-testid="stButton"] {
                        text-align: right;
                    }
                </style>
            """, unsafe_allow_html=True)
            if st.button("🚀 &nbsp;Prefill Form"): 
                with st.spinner("Prefilling form ..."):
                    try:
                        # Step 1: Parse the main form
                        parsed_form = parse_pdf_form(st.session_state.main_form_path)

                        # Step 2: Load support documents (async)
                        docs_data = asyncio.run(context_loader(st.session_state.support_doc_paths))

                        # Step 3: Pre-fill form using AI (async)
                        st.session_state.form_draft = asyncio.run(prefill_in_memory_form(parsed_form, docs_data))
                
                        st.toast("✅ Form successfully prefilled!")

                    except Exception as e:
                        st.toast(f"❌ Something went wrong. I just let know my boss.")

        with col_c:
            if st.session_state.form_draft:
                filled_pdf_bytes = fill_pdf_form(st.session_state.main_form_path, st.session_state.form_draft)
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


# ---------- User Chat ----------
# Initialize the chat graph
if 'chat_graph' not in st.session_state:
    st.session_state.chat_graph = create_chat_graph()
    st.session_state.messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        AIMessage(content=DEFAULT_AI_GREETING)]

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
    st.session_state.messages.append(user_message)

    # Display user message in chat history immediately
    with chat_container:
        with st.chat_message("user"):
            st.write(prompt)
    
    # Create agent state
    state = ChatAgentState(
        messages=st.session_state.messages, 
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
