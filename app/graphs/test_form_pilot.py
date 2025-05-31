import os
import pytest
from app.graphs.form_pilot import parse_pdf_form, create_agent_state

def test_parse_pdf_form_sample():
    # Path to the sample PDF form
    sample_form_path = os.path.join('app', 'docs', 'forms', 'form-example.pdf')
    # Initialize AgentState
    state = create_agent_state(form_filepath=sample_form_path)
    # Call the function
    result = parse_pdf_form(state)
    # Assert the top-level keys
    assert 'form_data' in result
    form_data = result['form_data']
    assert form_data['formFileName'] == sample_form_path
    assert 'fields' in form_data
    assert isinstance(form_data['fields'], list)
    # Optionally, check for at least one field (structure only)
    if form_data['fields']:
        field = form_data['fields'][0]
        assert 'label' in field
        assert 'type' in field
        assert 'value' in field 