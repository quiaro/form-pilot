import PyPDF2
import io
import streamlit as st


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
