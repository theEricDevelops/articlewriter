from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Union

class OutlineElementMetadata(BaseModel):
    element: str = "metadata"
    title: str
    subtitle: str
    author: str
    date: str  # ISO format, e.g., "2021-09-30"
    word_count: int

class OutlineElementIntroduction(BaseModel):
    element: str = "introduction"
    word_count: int
    section_heading: Optional[str] = None
    content: Dict[str, str]  # e.g., {"hook": "...", "topic_introduction": "..."}

class OutlineElementBodySection(BaseModel):
    word_count: int
    section_heading: str
    content: List[str]  # List of subpoints

class OutlineElementBody(BaseModel):
    element: str = "body"
    sections: List[OutlineElementBodySection]

class OutlineElementConclusion(BaseModel):
    element: str = "conclusion"
    word_count: int
    section_heading: Optional[str] = None
    content: Dict[str, str]  # e.g., {"summary": "...", "call_to_action": "..."}

class OutlineInstructions(BaseModel):
    formatting_and_engagement: Dict[str, str]
    seo_considerations: Dict[str, str]

class OutlineCreate(BaseModel):
    """Model for creating a new outline."""
    structure: List[Union[OutlineElementMetadata, OutlineElementIntroduction, 
                          OutlineElementBody, OutlineElementConclusion]]
    instructions: Optional[OutlineInstructions] = None
    topic_id: int

class OutlineUpdate(BaseModel):
    """Model for updating an existing outline."""
    structure: Optional[List[Union[OutlineElementMetadata, OutlineElementIntroduction, 
                                   OutlineElementBody, OutlineElementConclusion]]] = None
    instructions: Optional[OutlineInstructions] = None
    topic_id: Optional[int] = None

class OutlineResponse(BaseModel):
    """Model for returning outline data in API responses."""
    id: int
    structure: List[Union[OutlineElementMetadata, OutlineElementIntroduction, 
                          OutlineElementBody, OutlineElementConclusion]]
    instructions: Optional[OutlineInstructions] = None
    created_at: datetime
    updated_at: datetime
    topic_id: int
    article_ids: List[int]

    class Config:
        from_attributes = True