from typing import TypedDict

class SupportDoc(TypedDict):
    docId: str  # filepath + timestamp
    docType: str  # "word", "pdf", or "text"
    dateCreated: str  # ISO format timestamp
    content: str  # The text content of the document