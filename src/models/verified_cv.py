from pydantic import BaseModel, Field
from typing import List, Optional


class WorkExperience(BaseModel):
    company_name: str
    company_scope: Optional[str]
    company_location: Optional[str]
    position: str
    position_scope: str
    dates: str
    responsibilities: Optional[List[str]]


class CVForm(BaseModel):
    name: Optional[str]
    desirable_positions: Optional[List[str]]
    email: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    education: Optional[List[str]]
    work_experience: Optional[List[str]]
    skills: Optional[List[str]]
    languages: Optional[List[str]]
    achievements: Optional[List[str]]
    other: Optional[List[str]]


class ProbablyCV(BaseModel):
    reasoning: str = Field(description="Write down why do you think it could be CV or not")
    is_cv: bool
    form: Optional[CVForm]


class ProbablyCVWithRawText(ProbablyCV):
    raw_text: str
