from datetime import datetime
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
import PyPDF2
from app.models import SupportDoc

def word_document_loader(filepath: str) -> SupportDoc:
    """
    Load a Word document into a doc dictionary
    """
    # Return only the filename as the docId
    doc_id = filepath.split("/")[-1]
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    docs = list(UnstructuredWordDocumentLoader(filepath, mode="single").lazy_load())
    content = "".join([doc.page_content for doc in docs])
    return {
        "docId": doc_id,
        "docType": "docx",
        "dateCreated": date_created,  
        "content": content
    }

def pdf_document_loader(filepath: str) -> SupportDoc:
    """
    Load a PDF document into a doc dictionary
    """
    doc_id = filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S")
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
                
        return {
            "docId": doc_id,
            "docType": "pdf",
            "dateCreated": date_created,
            "content": content.strip()
        }
    except Exception as e:
        raise Exception(f"Error loading PDF: {str(e)}")

def text_document_loader(filepath: str) -> SupportDoc:
    """
    Load a text file into a doc dictionary
    """
    doc_id = filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S")
    date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "docId": doc_id,
            "docType": "text",
            "dateCreated": date_created,
            "content": content.strip()
        }
    except Exception as e:
        raise Exception(f"Error loading text file: {str(e)}")