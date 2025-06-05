import re
from typing import Dict, List
from app.models import DraftForm, FormField

def is_form_question(message: str) -> bool:
    """
    Check if the message is a question about a form field.
    The message should be of the form: [<number> fields left] <question_text>
    """
    pattern = r'^\[\d+ fields left\].*\?$'
    return bool(re.match(pattern, message))

def update_draft_form(draft_form: DraftForm, message: str) -> DraftForm:
    """
    Update the draft form with the user's response.
    We assume that the fields are in the same order as they are being asked by the `form_completion_node`
    (see `app/chat_agent/graph.py`)
    """
    # TODO: Make this implementation more robust. It would be good to refactor with the code in `form_completion_node`
    for i, field in enumerate(draft_form["fields"]):
        # Check for the first unanswered field
        # TODO: Extend this to support other field types
        if field["value"] == "" and field["type"] == "text":
            draft_form["fields"][i]["value"] = message
            break
    return draft_form

def get_prefilled_fields_status(previous_form: DraftForm, current_form: DraftForm) -> Dict[str, List[FormField]]:
    """
    Compare the previous and current form fields.

    Returns a dictionary with the following keys:
    - prefilled_fields: List[FormField]
    - empty_fields: List[FormField]
    """
    prefilled_fields = []
    empty_fields = []

    for i, field in enumerate(previous_form["fields"]):
        # TODO: Extend this to support other field types
        if field["value"] == "" and field["type"] == "text":
            if (previous_form["fields"][i]["value"] == current_form["fields"][i]["value"]):
                empty_fields.append(field)
            else:
                prefilled_fields.append(current_form["fields"][i])
    return {
        "prefilled_fields": prefilled_fields,
        "empty_fields": empty_fields
    }