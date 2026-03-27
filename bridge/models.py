from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

AgentRole = Literal["frontend", "backend", "orchestrator", "test_e2e"]

FeatureStatus = Literal[
    "created",
    "planning",
    "dispatching",
    "in_progress",
    "blocked",
    "awaiting_human_input",
    "resolved",
    "failed",
]

TaskStatus = Literal[
    "pending",
    "claimed",
    "in_progress",
    "blocked",
    "completed",
    "failed",
    "cancelled",
]

ContractType = Literal["api", "payload", "schema", "data_model", "other"]

ArtifactType = Literal[
    "file_reference",
    "payload",
    "log",
    "test",
    "validation_output",
    "other",
]

EventType = Literal[
    "feature_created",
    "feature_dispatched",
    "task_created",
    "task_claimed",
    "task_completed",
    "task_failed",
    "task_blocked",
    "contract_created",
    "artifact_created",
    "decision_created",
    "feature_blocked",
    "awaiting_human_input",
    "feature_resolved",
    "feature_failed",
    "tasks_queued",
    "human_input_received",
]


class Feature(BaseModel):
    feature_id: str
    title: str
    description: str
    status: FeatureStatus = "created"
    acceptance_criteria: list[str] = Field(default_factory=list)
    linked_case_ids: list[str] = Field(default_factory=list)
    blocking_reason: Optional[str] = None
    human_input_question: Optional[str] = None
    created_at: str
    updated_at: str


class Task(BaseModel):
    task_id: str
    feature_id: str
    title: str
    description: str
    owner_role: AgentRole
    status: TaskStatus = "pending"
    dependencies: list[str] = Field(default_factory=list)
    linked_case_id: Optional[str] = None
    created_at: str
    updated_at: str
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    result_summary: Optional[str] = None


class Contract(BaseModel):
    contract_id: str
    feature_id: str
    title: str
    description: str
    contract_type: ContractType
    definition: dict[str, Any]
    version: str = "1.0"
    created_at: str
    updated_at: str


class Artifact(BaseModel):
    artifact_id: str
    task_id: str
    feature_id: str
    artifact_type: ArtifactType
    title: str
    content: str
    created_by: AgentRole
    created_at: str


class Decision(BaseModel):
    decision_id: str
    feature_id: str
    title: str
    context: str
    decision: str
    rationale: str
    alternatives: list[str] = Field(default_factory=list)
    made_by: AgentRole
    created_at: str


class Event(BaseModel):
    event_id: str
    feature_id: str
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str
