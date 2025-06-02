from typing import List, Dict
from datetime import datetime
from app.context.document_loaders import word_document_loader, pdf_document_loader, text_document_loader
from app.models import SupportDoc

async def context_loader(docs_filepaths: List[str]) -> List[SupportDoc]:
    """
    Load the contents of all supporting documents into a data structure in memory
    """
    docs_data = []
    
    print(f"\nLoading {len(docs_filepaths)} documents...")
    
    for filepath in docs_filepaths:
        print(f"\nProcessing document: {filepath}")
        try:
            if filepath.endswith(".docx"):
                doc_data = word_document_loader(filepath)
            elif filepath.endswith(".pdf"):
                doc_data = pdf_document_loader(filepath)
            elif filepath.endswith(".txt"):
                doc_data = text_document_loader(filepath)
            else:
                print(f"Warning: Unsupported file type: {filepath}")
                continue
                
            if doc_data and doc_data.get("content"):
                print(f"Successfully loaded document. Content length: {len(doc_data['content'])} characters")
                print("First 200 characters of content:")
                print(doc_data['content'][:200] + "...")
                docs_data.append(doc_data)
            else:
                print(f"Warning: No content extracted from {filepath}")
                
        except Exception as e:
            print(f"Error loading document {filepath}: {str(e)}")
            docs_data.append({
                "docId": filepath + "__" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "docType": "error",
                "dateCreated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content": f"Error loading document: {str(e)}"
            })

    if not docs_data:
        raise ValueError("No valid documents were loaded")

    total_length = sum(len(doc["content"]) for doc in docs_data)
    print(f"\nTotal content length across all documents: {total_length} characters")
    
    if total_length > 204800:
        print(f"Warning: Total document length ({total_length}) exceeds recommended limit (204800)")
    
    return docs_data