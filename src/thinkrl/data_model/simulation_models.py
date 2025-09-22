from typing import Literal, Optional
from pydantic import BaseModel, Field

from tau2.data_model.simulation import Info
from tau2.data_model.message import Message
from tau2.domains.telecom.utils import get_now


class Judgment(BaseModel):
    """An LLM judge's evaluation of a user conversation's with a LLM agent."""

    verdict: Literal["PASS", "FAIL"] = Field(
        description="Either PASS or FAIL based on evaluation criteria"
    )
    debug_info: Optional[str] = Field(
        description="Explanation of why the verdict was reached to aid in a developer in identifying what went wrong (or right) so they can fix the issue. Includes specific messages locations (the jq query to find the data within the messages input) and evidence (specific violations of the policy or criteria not met).",
        default=None
    )
    reasoning: Optional[str] = Field(
        description="The chain of thought that led to the verdict and debug_info",
        default=None
    )
    judge_model: Optional[str] = Field(
        description="The model used for judging",
        default=None
    )
    timestamp: Optional[str] = Field(
        description="When the judgment was made (as a str dumped from a datetime object, e.g., from datetime.now())",
        default=None
    )

class SimulationOutput(BaseModel):
    """
    Simulation run for the given task.
    """

    id: str = Field(description="The unique identifier for the simulation run.")
    task_id: str = Field(description="The unique identifier for the task.")
    timestamp: str = Field(
        description="The timestamp of the simulation.", default_factory=get_now
    )
    start_time: str = Field(description="The start time of the simulation.")
    end_time: str = Field(description="The end time of the simulation.")
    duration: float = Field(description="The duration of the simulation.")
    messages: list[Message] = Field(
        description="The messages exchanged between the user, agent and environment."
    )
    judgment: Optional[Judgment] = Field(
        description="The LLM judge evaluation of this simulation run",
        default=None
    )
    is_reviewed: Optional[bool] = Field(
        description="Whether this simulation has been reviewed by the agent RL",
        default=False
    )

class FilteredSimulationRuns(BaseModel):
    """Filtered simulation results that may include judgments."""

    timestamp: Optional[str] = Field(
        description="The timestamp of the simulation results",
        default=None
    )
    info: Info = Field(description="Information about the simulation")
    simulations: list[SimulationOutput] = Field(
        description="The list of simulation outputs with LLM judge assessments"
    )