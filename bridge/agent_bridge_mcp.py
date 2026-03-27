from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field

from mcp.server.fastmcp import FastMCP

from store import BridgeStore

ROOT = Path(__file__).resolve().parent.parent / "agent_bridge_data"
store = BridgeStore(ROOT)

mcp = FastMCP("agent-bridge")


@mcp.tool()
def create_case(
    case_id: str = Field(description="Unique case ID, e.g. checkout-502-001"),
    title: str = Field(description="Short case title"),
    problem: str = Field(description="Detailed problem statement"),
) -> dict:
    """Create a new investigation case."""
    return store.create_case(case_id=case_id, title=title, problem=problem)


@mcp.tool()
def list_cases() -> list[dict]:
    """List all known cases."""
    return store.list_cases()


@mcp.tool()
def get_case(case_id: str = Field(description="Case ID")) -> dict:
    """Get case state for a specific investigation."""
    return store.get_case(case_id)


@mcp.tool()
def post_message(
    case_id: str = Field(description="Case ID"),
    from_agent: Literal["frontend", "backend", "orchestrator"] = Field(description="Sender"),
    to_agent: Literal["frontend", "backend", "all"] = Field(description="Recipient"),
    message_type: Literal[
        "question",
        "finding",
        "hypothesis",
        "request_for_repro",
        "proposed_fix",
        "resolved",
        "blocked",
    ] = Field(description="Message type"),
    summary: str = Field(description="One-paragraph summary"),
    evidence: list[str] = Field(default_factory=list, description="Concrete evidence list"),
    hypothesis: str | None = Field(default=None, description="Optional hypothesis"),
    question: str | None = Field(default=None, description="Optional question"),
    priority: Literal["low", "medium", "high"] = Field(default="medium", description="Priority"),
) -> dict:
    """Post a structured update to the shared case room."""
    return store.post_message(
        case_id=case_id,
        from_agent=from_agent,
        to_agent=to_agent,
        msg_type=message_type,
        summary=summary,
        evidence=evidence,
        hypothesis=hypothesis,
        question=question,
        priority=priority,
    )


@mcp.tool()
def get_messages(
    case_id: str = Field(description="Case ID"),
    agent: Literal["frontend", "backend", "orchestrator"] | None = Field(
        default=None,
        description="Optional agent filter. When provided, returns messages visible to that agent.",
    ),
) -> list[dict]:
    """Get messages for a case, optionally filtered for one agent's view."""
    return store.get_messages(case_id=case_id, agent=agent)


@mcp.tool()
def resolve_case(
    case_id: str = Field(description="Case ID"),
    root_cause: str = Field(description="Precise root cause"),
    proposed_fix: str = Field(description="Recommended fix"),
    validation_steps: list[str] = Field(default_factory=list, description="Validation checklist"),
) -> dict:
    """Resolve a case with root cause, fix, and validation steps."""
    return store.resolve_case(
        case_id=case_id,
        root_cause=root_cause,
        proposed_fix=proposed_fix,
        validation_steps=validation_steps,
    )


@mcp.tool()
def export_case_summary(case_id: str = Field(description="Case ID")) -> str:
    """Export a markdown summary for the case and return it."""
    return store.export_summary(case_id)


if __name__ == "__main__":
    mcp.run()
