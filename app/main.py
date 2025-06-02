import streamlit as st
import os
import sys
import asyncio
from typing import List
from datetime import datetime
import json
import io

# Add /app/graphs to Python path so we can import modules
# sys.path.append(os.path.join(os.path.dirname(__file__), "graphs"))

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
if "filled_form" not in st.session_state:
    st.session_state.filled_form = None

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
            for key in ["main_form_path", "support_doc_paths", "chat_history", "filled_form"]:
                st.session_state[key] = None if "path" in key else []
            st.rerun()

# ---------- Main Section: Assistant Chat ----------
st.title("🧠 Form Assistant Chat")

if st.session_state.main_form_path and st.session_state.support_doc_paths:
    if st.button("🚀 Run AI Assistant"):
        with st.spinner("⏳ Processing form and documents..."):
            try:
                # Step 1: Parse the main form
                parsed_form = parse_pdf_form(st.session_state.main_form_path)

                # Step 2: Load support documents (async)
                docs_data = asyncio.run(context_loader(st.session_state.support_doc_paths))

                # Step 3: Pre-fill form using AI (async)
                st.session_state.filled_form = asyncio.run(prefill_in_memory_form(parsed_form, docs_data))

                st.success("✅ Form filled successfully!")

            except Exception as e:
                st.error(f"❌ Error running assistant: {str(e)}")

# ---------- Display Filled Form ----------
if st.session_state.filled_form:
    st.subheader("📄 Filled Form Preview")
    for field in st.session_state.filled_form["fields"]:
        label = field.get("label", "Unnamed Field")
        value = field.get("value", "")
        st.markdown(f"**{label}:** {value if value else '*Not Filled*'}")
    
    # Add download buttons for both JSON and PDF formats
    col1, col2 = st.columns(2)
    
    with col1:
        # JSON download
        json_str = json.dumps(st.session_state.filled_form, indent=2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"filled_form_{timestamp}.json"
        
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name=json_filename,
            mime="application/json",
            help="Download the filled form data in JSON format"
        )
    
    with col2:
        # PDF download
        try:
            filled_pdf_bytes = fill_pdf_form(st.session_state.main_form_path, st.session_state.filled_form)
            pdf_filename = f"filled_form_{timestamp}.pdf"
            
            st.download_button(
                label="📄 Download as PDF",
                data=filled_pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                help="Download the filled form in PDF format"
            )
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")

# ---------- User Q&A Chat (Optional for follow-up) ----------
if st.session_state.filled_form and st.session_state.support_doc_paths:
    user_question = st.text_input("Ask a follow-up question:", key="user_question")
    if st.button("Submit"):
        if user_question.strip():
            st.session_state.chat_history.append(("user", user_question))
            # Replace with real follow-up logic if needed
            st.session_state.chat_history.append(("assistant", "🤖 (This is a placeholder response.)"))
        else:
            st.warning("Please enter a question before submitting.")

    for role, msg in st.session_state.chat_history:
        st.markdown(f"**{role.capitalize()}:** {msg}")
else:
    st.info("👈 Please upload the required documents and run the assistant to begin.")
