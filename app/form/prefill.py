from typing import Dict, List
import os
import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from app.models import SupportDoc
from app.utils.llm import get_llm

def doc_data_to_string(doc_data: Dict) -> str:
    """
    Convert a document data dictionary to a string

    Returns:
        A string of the form:
        <reference_start>
           Document ID: {doc_data['docId']}
           Content: {doc_data['content']}
        <reference_end>
    """
    return f"""
    <reference>
        <document_id>
            {doc_data['docId']}
        </document_id>
        <content>
            {doc_data['content']}
        </content>
    </reference>
    """


def parse_llm_response(response):
    try:
        data = json.loads(response.strip())
        # Ensure required keys exist with defaults
        return {
            "value": data.get("value", ""),
            "docId": data.get("docId")
        }
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}")


async def text_field_processor(field: Dict, context: str) -> Dict:
    """
    Uses an LLM to find the answer to the field using the context data. If the context data is not enough for filling the field, leave the field empty.
    """
    llm = get_llm("PREFILL_LLM")

    PROMPT = """
        You are a helpful assistant whose task is to answer a field in a form to the best of your ability.
        You are given information about the field and context to answer. 
        You can only use the context to answer the field.

        Respond with valid JSON only. Do not wrap in code blocks or add explanatory text.

        Examples of correct responses:
        {{"value": "John Smith", "docId": "doc123"}}
        {{"value": "", "docId": null}}

        Rules:
        - If context lacks information: {{"value": "", "docId": null}}
        - If context has information: {{"value": "your_answer", "docId": "source_document_id"}}
        - Use null (not None) for missing docId
        - Keep answers succinct

        Field information: 
        - Label: {field[label]}
        - Description: {field[description]}
        - Type: {field[type]}

        Context: {context}
    """
    rag_prompt = ChatPromptTemplate.from_template(PROMPT)
    messages = rag_prompt.format_messages(field=field, context=context)

    response = await llm.ainvoke(messages)
    output_field = field.copy()
    parsed_response = parse_llm_response(response.content)
    output_field["value"] = parsed_response["value"]
    output_field["docId"] = parsed_response["docId"]
    output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return output_field


def checkbox_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a checkbox field
    """
    # TODO: Implement checkbox field processor
    output_field = field.copy()
    return output_field


def dropdown_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a dropdown field
    """
    # TODO: Implement checkbox field processor
    output_field = field.copy()
    return output_field


async def prefill_in_memory_form(form_data: Dict, docs_data: List[SupportDoc]) -> Dict:
    """
    Loops through all form fields and calls the corresponding field processor for each field.

    Args:
        form_data: The form data to prefill
        docs_data: The supporting documents to use for context

    Returns:
        A dictionary with the updated form data
    """
    form_fields = form_data["fields"]
    output_form = form_data.copy()
    output_fields = []
    # supporting documents
    context = "\n".join([doc_data_to_string(doc) for doc in docs_data])

    for field in form_fields:
        output_field = field.copy()  # Always start with a copy

        try:
            if field["type"] == "text":
                output_field = await text_field_processor(field, context)
            elif field["type"] == "checkbox":
                output_field = checkbox_field_processor(field, context)
            elif field["type"] == "dropdown":
                output_field = dropdown_field_processor(field, context)
            else:
                raise ValueError(f"Unsupported field type: {field['type']}")
        except Exception as e:
            output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_field["error"] = str(e)

        output_fields.append(output_field)

    output_form["fields"] = output_fields
    return output_form
