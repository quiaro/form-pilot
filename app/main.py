import streamlit as st
import os
import sys
import asyncio
from typing import List
from datetime import datetime
import json
import io
from langchain_core.messages import HumanMessage, AIMessage
from app.chat_agent.graph import create_chat_graph, ChatAgentState

from app.doc_handlers.pdf import parse_pdf_form, fill_pdf_form
from app.context.loader import context_loader
from app.form.prefill import prefill_in_memory_form

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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "prefilled_form" not in st.session_state:
    st.session_state.prefilled_form = None

# ---------- Sidebar: File Uploads ----------
with st.sidebar:
    st.title("📂 Document Panel")

    st.subheader("1️⃣ Upload Main Form")
    main_form = st.file_uploader(
        "Upload the main document (PDF, DOCX, TXT, or Image)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="main_form_uploader"
    )
    if main_form:
        st.session_state.main_form_path = save_uploaded_file(main_form)
        st.markdown(f"**✅ Uploaded:** `{main_form.name}`")

    st.divider()

    st.subheader("2️⃣ Upload Support Documents")
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
            for key in ["main_form_path", "support_doc_paths", "chat_history", "prefilled_form"]:
                st.session_state[key] = None if "path" in key else []
            st.rerun()

# ---------- Main Section: Assistant Chat ----------
st.title("🧑‍🚀 Form Pilot", anchor=False)

if st.session_state.main_form_path and st.session_state.support_doc_paths:
    if st.button("🚀 Prefill Form"):
        with st.spinner("⏳ Processing form and documents..."):
            try:
                # Step 1: Parse the main form
                parsed_form = parse_pdf_form(st.session_state.main_form_path)

                # Step 2: Load support documents (async)
                docs_data = asyncio.run(context_loader(st.session_state.support_doc_paths))

                # Step 3: Pre-fill form using AI (async)
                st.session_state.prefilled_form = asyncio.run(prefill_in_memory_form(parsed_form, docs_data))

                # Add download buttons for both JSON and PDF formats
                col1, col2 = st.columns(2)

                with col1:
                    st.success("✅ Form filled successfully!")

                with col2:
                    # PDF download
                    try:
                        filled_pdf_bytes = fill_pdf_form(st.session_state.main_form_path, st.session_state.prefilled_form)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_filename = f"form_{timestamp}.pdf"
                        
                        st.download_button(
                            label="📄 Download Prefilled PDF",
                            data=filled_pdf_bytes,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            help="Download the filled form in PDF format"
                        )
                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")

            except Exception as e:
                st.error(f"❌ Error running assistant: {str(e)}")


# ---------- User Q&A Chat ----------
# Initialize the chat graph
if 'chat_graph' not in st.session_state:
    st.session_state.chat_graph = create_chat_graph()
    st.session_state.messages = []

# Chat interface
chat_container = st.container(height=620)

# TODO: Decide if this is needed
# if st.session_state.prefilled_form and st.session_state.support_doc_paths:

# Display chat message history
with chat_container:
    for message in st.session_state.messages:
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.write(message.content)

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to session state
    user_message = HumanMessage(content=prompt)
    st.session_state.messages.append(user_message)
    
    # # Display user message immediately
    with st.chat_message("user"):
        st.write(prompt)
    
    # Create agent state
    state = ChatAgentState(messages=st.session_state.messages)
    
    # Process with the graph
    with st.chat_message("assistant"):
        # with st.spinner("Thinking..."):
        result = st.session_state.chat_graph.invoke(state)
        
        # Get the assistant's response
        assistant_message = result["messages"][-1]
        st.write(assistant_message.content)
        
        # Update session state
        st.session_state.messages = result["messages"]
        st.rerun()
