from typing import Dict, List, Any, Tuple
import os
import json
import re
import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from app.models import SupportDoc
from app.utils.llm import get_llm

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_house_number(address: str) -> str:
    """
    Extract house number from an address string.
    """
    match = re.search(r'\b\d+\b', address)
    return match.group() if match else ""

def clean_field_value(value: str, field_type: str) -> str:
    """
    Clean and format field values based on their type.
    """
    if not value:
        return ""
    
    value = str(value).strip()
    
    # Remove any extra whitespace
    value = re.sub(r'\s+', ' ', value)
    
    # Handle specific field types
    if field_type == "house_number":
        return extract_house_number(value)
    elif field_type == "postal_code":
        # Remove any non-alphanumeric characters
        return re.sub(r'[^A-Za-z0-9]', '', value)
    elif field_type == "phone":
        # Remove any non-digit characters
        return re.sub(r'[^\d]', '', value)
    elif field_type == "email":
        # Ensure valid email format
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, value)
        return match.group() if match else ""
    elif field_type == "height":
        # Extract numbers only
        match = re.search(r'\b\d+\b', value)
        return match.group() if match else ""
    
    return value

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
    Uses an LLM to find the answer to the field using the context data.
    """
    llm = get_llm("PREFILL_LLM")

    # Determine field type for cleaning
    field_type = field.get("type", "").lower()
    field_label = field.get("label", "").lower()
    
    # Special handling for house number fields
    if field_label in ["house nr", "house number"]:
        field_type = "house_number"
    # Map other field labels to specific types for cleaning
    elif "postal" in field_label or "zip" in field_label:
        field_type = "postal_code"
    elif "phone" in field_label or "mobile" in field_label:
        field_type = "phone"
    elif "email" in field_label:
        field_type = "email"
    elif "height" in field_label:
        field_type = "height"

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
        - For country fields, use the exact country name as specified in the context
        - For dates, use YYYY-MM-DD format
        - For numbers, use the exact number without formatting
        - For height, use the exact number provided
        - For house numbers, extract only the number
        - For postal codes, use only alphanumeric characters
        - For phone numbers, use only digits
        - For emails, ensure valid email format

        Field information: 
        - Label: {field[label]}
        - Description: {field[description]}
        - Type: {field[type]}

        Context: {context}

        Think carefully about the field label and description to determine what information is being asked for.
        If the field is asking for a specific type of information (like country, date, etc.), make sure to format the answer appropriately.
        Pay special attention to exact values mentioned in the context.
    """
    rag_prompt = ChatPromptTemplate.from_template(PROMPT)
    messages = rag_prompt.format_messages(field=field, context=context)

    response = await llm.ainvoke(messages)
    output_field = field.copy()
    parsed_response = parse_llm_response(response.content)
    
    # Special handling for house number fields
    if field_label in ["house nr", "house number"]:
        output_field["value"] = extract_house_number(parsed_response["value"])
    else:
        # Clean the value based on field type
        cleaned_value = clean_field_value(parsed_response["value"], field_type)
        output_field["value"] = cleaned_value
    
    output_field["docId"] = parsed_response["docId"]
    output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return output_field


def format_pdf_value(value: Any, field_type: str, options: List[str] = None) -> Any:
    logger.info(f"Formatting value: {value} for field type: {field_type}")
    if options:
        logger.info(f"Available options: {options}")

    if field_type == "checkbox_group":
        if isinstance(value, list):
            return [str(v) if v in ["/Yes", "/Off"] else "/Off" for v in value]
        return ["/Off"]
    elif field_type == "dropdown":
        if isinstance(value, list):
            value = next((v for v in value if v), "")
        if options:
            match = next((opt for opt in options if opt.lower() == str(value).lower()), options[0])
            logger.info(f"Matched dropdown value: {match} from input: {value}")
            return match
        return str(value) if value is not None else ""
    elif field_type == "list_box":
        if isinstance(value, list):
            clean = [str(v) for v in value if v in (options or [])]
            return clean if clean else [options[0]] if options else []
        return [str(value)] if value in (options or []) else [options[0]] if options else []
    else:
        return str(value) if value is not None else ""


async def checkbox_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a checkbox field using the LLM.
    """
    llm = get_llm("PREFILL_LLM")
    
    PROMPT = """
        You are a helpful assistant whose task is to determine if a checkbox should be checked based on the context.
        You are given information about the checkbox and context to make the decision.
        You can only use the context to make the decision.

        Respond with valid JSON only. Do not wrap in code blocks or add explanatory text.

        Examples of correct responses:
        {{"value": "/Yes", "docId": "doc123"}}
        {{"value": "/Off", "docId": null}}
        {{"value": ["/Yes", "/Off", "/Yes"], "docId": "doc123"}}

        Rules:
        - If context lacks information: {{"value": "/Off", "docId": null}}
        - If context has information: {{"value": "/Yes" or "/Off", "docId": "source_document_id"}}
        - Use null (not None) for missing docId
        - For checkbox groups, return a list of "/Yes" or "/Off" values
        - Mark as "/Yes" ONLY if:
          * The context EXPLICITLY states the condition is true
          * For driving license: ONLY if the context explicitly mentions having a license
          * For language checkboxes: ONLY if the context explicitly mentions knowing that specific language
        - Mark as "/Off" if:
          * The context does not explicitly state the condition is true
          * The context implies but does not explicitly state the condition
          * There's no clear indication in the context
          * The context is ambiguous

        Field information: 
        - Label: {field[label]}
        - Description: {field[description]}
        - Type: {field[type]}
        - Options: {field[options]}

        Context: {context}

        Think carefully about the field label and description to determine if the checkbox should be checked.
        Pay special attention to exact values and conditions mentioned in the context.
        For checkbox groups, carefully evaluate each option against the context.
        For driving license, ONLY check if the context explicitly mentions having a license.
        For language checkboxes, ONLY check if the context explicitly mentions knowing that specific language.
        When in doubt, mark as "/Off".
    """
    
    rag_prompt = ChatPromptTemplate.from_template(PROMPT)
    messages = rag_prompt.format_messages(field=field, context=context)
    
    response = await llm.ainvoke(messages)
    output_field = field.copy()
    parsed_response = parse_llm_response(response.content)
    
    # Handle both single checkboxes and checkbox groups
    if isinstance(parsed_response["value"], list):
        output_field["value"] = format_pdf_value(parsed_response["value"], field["type"])
    else:
        output_field["value"] = format_pdf_value([parsed_response["value"]], field["type"])
    
    output_field["docId"] = parsed_response["docId"]
    output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return output_field


async def dropdown_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a dropdown field using the LLM.
    """
    # TODO: Test implementation
    try:
        # Extract information from context
        prompt = f"""Select the most appropriate option for {field['label']} from the following options: {field['options']}
        Based on the context: {context}
        Return only the selected option."""
        
        response = await get_llm().ainvoke(prompt)
        value = response.content.strip()
        
        # Validate the response is in the options list
        if value not in field["options"]:
            value = field["options"][0]
        
        return {
            "label": field["label"],
            "type": field["type"],
            "value": format_pdf_value(value, field["type"], field["options"]),
            "options": field["options"]
        }
    except Exception as e:
        return {
            "label": field["label"],
            "type": field["type"],
            "value": field["options"][0] if field["options"] else "",
            "options": field["options"]
        }


async def list_box_field_processor(field: Dict, context: str) -> Dict:
    """
    Process a list box field using the LLM.
    """
    llm = get_llm("PREFILL_LLM")
    
    PROMPT = """
        You are a helpful assistant whose task is to select the appropriate option(s) for a list box field.
        You are given information about the field, its options, and context to make the selection.
        You can only use the context to make the selection.

        Respond with valid JSON only. Do not wrap in code blocks or add explanatory text.

        Examples of correct responses:
        For dropdown (single select):
        {{"value": "Option1", "docId": "doc123"}}

        For list box (multi select):
        {{"value": ["Option1", "Option2"], "docId": "doc123"}}

        Rules:
        - If context lacks information: {{"value": "", "docId": null}}
        - If context has information: {{"value": "selected_option" or ["option1", "option2"], "docId": "source_document_id"}}
        - Use null (not None) for missing docId
        - For dropdowns (single select), return a single value
        - For list boxes (multi select), return an array of values
        - Use exact option values as provided in the options list
        - Do not wrap single values in arrays for dropdowns

        Field information: 
        - Label: {field[label]}
        - Description: {field[description]}
        - Type: {field[type]}
        - Options: {field[options]}

        Context: {context}

        Think carefully about the field label and description to determine which option(s) should be selected.
        Pay special attention to exact values mentioned in the context.
        Only select options that are explicitly mentioned or clearly implied in the context.
    """
    
    rag_prompt = ChatPromptTemplate.from_template(PROMPT)
    messages = rag_prompt.format_messages(field=field, context=context)
    
    response = await llm.ainvoke(messages)
    output_field = field.copy()
    parsed_response = parse_llm_response(response.content)
    
    # For dropdowns, ensure we get a single value
    if field["type"] == "dropdown":
        if isinstance(parsed_response["value"], list):
            parsed_response["value"] = parsed_response["value"][0] if parsed_response["value"] else ""
    
    # Format the value based on field type
    output_field["value"] = format_pdf_value(parsed_response["value"], field["type"], field.get("options"))
    output_field["docId"] = parsed_response["docId"]
    output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    # Prepare context from documents
    context_parts = [doc_data_to_string(doc) for doc in docs_data]
    context = "\n".join(context_parts)

    # Process all fields
    for field in form_fields:
        output_field = field.copy()  # Always start with a copy

        try:
            if field["type"] == "text":
                output_field = await text_field_processor(field, context)
            elif field["type"] == "checkbox" or field["type"] == "checkbox_group":
                output_field = await checkbox_field_processor(field, context)
            elif field["type"] == "dropdown":
                output_field = await list_box_field_processor(field, context)
            elif field["type"] == "list_box":
                output_field = await list_box_field_processor(field, context)
            else:
                raise ValueError(f"Unsupported field type: {field['type']}")

        except Exception as e:
            output_field["lastProcessed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_field["error"] = str(e)

        output_fields.append(output_field)

    output_form["fields"] = output_fields
    return output_form