import streamlit as st
import os
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

# Streamlit Interface
st.set_page_config(page_title="AI Document Assistant", layout="wide")

# ------------------ Session Initialization ------------------ #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "reset" not in st.session_state:
    st.session_state.reset = False

# ------------------ Sidebar: File Upload Sections ------------------ #
with st.sidebar:
    st.title("📂 Document Panel")

    st.subheader("1️⃣ Upload Main Form")
    main_form = st.file_uploader(
        "Upload the main document (PDF, DOCX, TXT, or Image)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="main_form"
    )

    if main_form:
        st.markdown("**✅ Main form uploaded:**")
        st.code(main_form.name)

    st.divider()

    st.subheader("2️⃣ Upload Support Documents")
    support_docs = st.file_uploader(
        "Upload one or more support documents (PDF, DOCX, TXT, or Images)",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="support_docs"
    )

    if support_docs:
        st.markdown("**📎 Support documents uploaded:**")
        for idx, doc in enumerate(support_docs, 1):
            st.markdown(f"{idx}. `{doc.name}`")

    # Show Start Over if both uploads exist
    if main_form and support_docs:
        if st.button("🔄 Start Over"):
            # Clear session variables
            for key in ["main_form", "support_docs", "chat_history"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()

# ------------------ Main Area: Chat Interface ------------------ #
st.title("🧠 Form Assistant Chat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if main_form and support_docs:
    user_question = st.text_input("Ask a question about the documents:", key="user_question")

    if st.button("Submit"):
        if user_question.strip():
            st.session_state.chat_history.append(("user", user_question))
            # Placeholder response
            agent_response = "🤖 (This is a placeholder for the AI response.)"
            st.session_state.chat_history.append(("assistant", agent_response))
        else:
            st.warning("Please enter a question before submitting.")

    # Display chat history
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"**You:** {message}")
        else:
            st.markdown(f"**AI Assistant:** {message}")
else:
    st.info("👈 Please upload a main form and at least one support document to start asking questions.")
