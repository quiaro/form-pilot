from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class SupportDoc:
    docId: str  # filepath + timestamp
    docType: str  # "word", "pdf", or "text"
    dateCreated: str  # ISO format timestamp
    content: str  # The text content of the document

@dataclass
class FormField:
    label: str
    description: str
    type: str
    docId: Optional[str]
    value: str | List[str]
    options: List[str]
    lastProcessed: str
    lastSurveyed: str

@dataclass
class DraftForm:
    formFileName: str
    lastSaved: str
    fields: List[FormField]