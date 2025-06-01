import streamlit as st
import os
import sys
import asyncio
from typing import List
from datetime import datetime
import json
import PyPDF2
import io
from PyPDF2.generic import NameObject, ArrayObject, TextStringObject, IndirectObject

# Add /app/graphs to Python path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "graphs"))

from pre_fill_form import create_agent_state as create_prefill_state, build_graph as build_prefill_graph
from load_context import build_graph as build_context_graph
from form_pilot import parse_pdf_form

def fill_pdf_form(pdf_path: str, filled_form: dict) -> bytes:
    """
    Fill the PDF form with the provided data and return the filled PDF as bytes.
    Handles various types of PDF form fields including:
    - Text fields (/Tx)
    - Checkboxes (/Btn)
    - Radio buttons (/Btn)
    - Dropdown lists (/Ch)
    - List boxes (/Ch with multiple selection)
    - Formatted fields
    """
    try:
        # Read the original PDF
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            writer = PyPDF2.PdfWriter()
            
            # Copy all pages to the writer
            for page in reader.pages:
                writer.add_page(page)
            
            # Copy the form fields to the writer
            if "/AcroForm" in reader.trailer["/Root"]:
                writer._root_object.update({
                    PyPDF2.generic.NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
                })
            
            # Create a mapping of field names to their values
            field_values = {}
            for field in filled_form["fields"]:
                label = field["label"]
                value = field["value"]
                field_type = field["type"]
                
                # Handle different field types
                if field_type == "checkbox_group":
                    # For checkbox groups, we need to map each checkbox individually
                    if isinstance(value, list):
                        for i, checkbox_value in enumerate(value):
                            checkbox_name = field["options"][i] if i < len(field["options"]) else f"{label}_{i+1}"
                            field_values[checkbox_name] = checkbox_value
                elif field_type == "list_box":
                    # For list boxes, ensure we have a list of values
                    field_values[label] = value if isinstance(value, list) else [value]
                else:
                    # For other fields, use the value as is
                    field_values[label] = value
            
            # Update the writer's form fields
            writer.update_page_form_field_values(writer.pages[0], field_values)
            
            # Write to bytes buffer
            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
    except Exception as e:
        st.error(f"Error filling PDF form: {str(e)}")
        raise Exception(f"Error filling PDF form: {str(e)}")

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
                form_state = {"form_filepath": st.session_state.main_form_path}
                parsed_form = parse_pdf_form(form_state)["form_data"]

                # Step 2: Load support documents (async)
                context_graph = build_context_graph()
                context_result = asyncio.run(
                    context_graph.ainvoke({"docs_filepaths": st.session_state.support_doc_paths})
                )
                docs_data = context_result["docs_data"]

                # Step 3: Pre-fill form using AI (async)
                prefill_graph = build_prefill_graph()
                agent_input = create_prefill_state(form_data=parsed_form, docs_data=docs_data)
                result = asyncio.run(prefill_graph.ainvoke(agent_input))

                st.session_state.filled_form = result["filled_form"]
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
