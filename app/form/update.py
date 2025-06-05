import re
from app.models import DraftForm

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
