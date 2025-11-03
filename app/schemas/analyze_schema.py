from typing import Literal, Optional
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    input_text: str = Field(..., description="Security logs, access records, and/or policy text")
    output_format: Literal["json", "markdown"] = "json"
    schema: Literal["risk_assessment", "event_summary", "policy_alignment"] = "risk_assessment"
    # Optional hint to bound the analysis window or provide context strings
    time_window: Optional[str] = Field(None, description="ISO8601 range or descriptive window")
    inputs: Optional[list[str]] = Field(default=None, description='e.g. ["logs","access_records","policy_text"]')


class AnalyzeResponseJSON(BaseModel):
    """When output_format='json', we echo the parsed JSON back as dict."""
    data: dict

class AnalyzeResponseMarkdown(BaseModel):
    """When output_format='markdown', we return a markdown string."""
    markdown: str
