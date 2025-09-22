from typing import List, Optional
from pydantic import BaseModel, Field


class ImpactedTrace(BaseModel):
    """Model for traces impacted by the root cause."""
    id: str = Field(..., description="Unique identifier for the trace")
    task_id: str = Field(..., description="Task identifier associated with the trace")
    notes: List[str] = Field(default_factory=list, description="List of notes for this trace")


class WhatShouldBeFixed(BaseModel):
    """Model for describing what should be fixed."""
    changes_to_policy: List[str] = Field(default_factory=list, description="List of policy changes needed")
    changes_to_system_prompt: List[str] = Field(default_factory=list, description="List of system prompt changes needed")
    changes_to_tool_definitions: List[str] = Field(default_factory=list, description="List of tool definition changes needed")


class RootCause(BaseModel):
    """Model for root cause analysis."""
    description: str = Field(..., description="Description of the root cause")
    comments: List[str] = Field(default_factory=list, description="List of comments about the root cause")
    traces_impacted: List[ImpactedTrace] = Field(default_factory=list, description="List of traces impacted by this root cause")
    hypotheses: List['Hypothesis'] = Field(default_factory=list, description="List of hypotheses related to this root cause")


class Hypothesis(BaseModel):
    """Data model for hypothesis tracking and analysis."""
    root_cause: RootCause = Field(..., description="The root cause this hypothesis relates to")
    description: str = Field(..., description="Description of the hypothesis")
    comments: List[str] = Field(default_factory=list, description="List of comments about the hypothesis as you are reviewing the traces.")
    what_should_be_fixed: Optional[WhatShouldBeFixed] = Field(None, description="Description of what should be fixed based on this hypothesis")


# Update forward reference
RootCause.model_rebuild()