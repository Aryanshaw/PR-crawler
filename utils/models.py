from pydantic import BaseModel, Field
from typing import List, Optional

class UIElementModel(BaseModel):
    id: str = Field(description="Unique stable identifier for the element")
    type: str = Field(description="Type of element (button, input, link, etc.)")
    label: str = Field(description="Visible label or aria-label of the element")
    role: str = Field(description="ARIA role of the element")
    fingerprint: str = Field(description="Stable fingerprint (role + label + position context)")
    component_source: Optional[str] = Field(None, description="Inferred source component name if possible")

class UserActionModel(BaseModel):
    id: str = Field(description="Unique identifier for the action")
    description: str = Field(description="What this action does")
    trigger: str = Field(description="What triggers this action (click, hover, etc.)")
    outcome: str = Field(description="Expected outcome of this action")
    target_screen_url: Optional[str] = Field(None, description="URL this action navigates to, if any")

class ScreenAnalysisModel(BaseModel):
    id: str = Field(description="Unique ID for the screen (e.g., slugified title)")
    title: str = Field(description="Page title")
    purpose: str = Field(description="Semantic purpose of the screen")
    elements: List[UIElementModel] = Field(description="List of interactive elements found")
    actions: List[UserActionModel] = Field(description="List of user actions possible on this screen")

class RequirementModel(BaseModel):
    id: str = Field(description="Unique requirement ID (e.g., REQ-001)")
    text: str = Field(description="The requirement description")
    acceptance_criteria: str = Field(description="Acceptance criteria for this requirement")
    priority: str = Field(description="Priority (High, Medium, Low)")

class FeatureModel(BaseModel):
    id: str = Field(description="Unique feature ID")
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    requirements: List[RequirementModel] = Field(description="Requirements belonging to this feature")

class UserFlowModel(BaseModel):
    id: str = Field(description="Unique flow ID")
    name: str = Field(description="Flow name")
    steps: List[str] = Field(description="Ordered list of steps in the flow")
    requirement_ids: List[str] = Field(description="IDs of requirements involved in this flow")

class PRDAnalysisModel(BaseModel):
    features: List[FeatureModel] = Field(description="List of features found in the PRD")
    user_flows: List[UserFlowModel] = Field(description="List of user flows found in the PRD")
