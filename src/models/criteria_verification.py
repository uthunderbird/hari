from pydantic import BaseModel, Field


class Criteria(BaseModel):
    short_name: str
    description: str
    is_mandatory: bool = True


class Vacancy(BaseModel):
    language: str = Field(description="On which language original vacancy is written on.")
    plan: str = Field(description="Build a plan of the new vacancy text")
    text: str
    criteria_list: list[Criteria] = Field(description="Choose up to 7 most valuable criteria from the vacancy text. The list can't be empty!")


class CvCriteriaMatch(BaseModel):
    file_path: str
    matched_criteria_list: list[str]
    pros: list[str]
    cons: list[str]
    matching_rate_reasoning: str = Field(
        description="Explain why the candidate is a match for the vacancy or why not. "
                    "Please note that the explanation should be based not on criteria list "
                    "but on the text description of the vacancy. As well as matching rate. "
                    "Refer facts that will help candidate to succeed on this position from the "
                    "job description text provided and do not mention any criteria matches because "
                    "they will be obvious for the user.",
    )
    compare_with_other_candidates: str
    matching_rate: int
    candidate_name: str = "Unknown"
    contacts: list[str] | None = Field(default_factory=list)


class BulkCvCriteriaMatch(BaseModel):
    matches: list[CvCriteriaMatch]
