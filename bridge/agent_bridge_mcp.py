from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from mcp.server.fastmcp import FastMCP

from store import BridgeStore
from orchestrator import Coordinator

ROOT = Path(__file__).resolve().parent.parent / "agent_bridge_data"
store = BridgeStore(ROOT)
coordinator = Coordinator(store)

mcp = FastMCP("agent-bridge")


# ════════════════════════════════════════════════════════════════════════════
# CASE tools — backward-compatible debugging workflow
# ════════════════════════════════════════════════════════════════════════════


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
    """List all known investigation cases."""
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


# ════════════════════════════════════════════════════════════════════════════
# FEATURE tools — cross-repo delivery work units
# ════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_feature(
    feature_id: str = Field(description="Unique feature ID, e.g. feat-auth-refresh-001"),
    title: str = Field(description="Short feature title"),
    description: str = Field(description="Full description of the feature or fix"),
    linked_case_ids: list[str] = Field(
        default_factory=list,
        description="Optional case IDs this feature addresses",
    ),
) -> dict:
    """Create a new cross-repo feature or fix unit."""
    return store.create_feature(
        feature_id=feature_id,
        title=title,
        description=description,
        linked_case_ids=linked_case_ids,
    )


@mcp.tool()
def get_feature(
    feature_id: str = Field(description="Feature ID"),
) -> dict:
    """Get current state of a feature."""
    return store.get_feature(feature_id)


@mcp.tool()
def list_features() -> list[dict]:
    """List all features."""
    return store.list_features()


@mcp.tool()
def update_feature_status(
    feature_id: str = Field(description="Feature ID"),
    status: Literal[
        "created",
        "planning",
        "dispatching",
        "in_progress",
        "blocked",
        "awaiting_human_input",
        "resolved",
        "failed",
    ] = Field(description="New status"),
) -> dict:
    """Manually update a feature's lifecycle status."""
    return store.update_feature(feature_id, status=status)


@mcp.tool()
def add_feature_acceptance_criteria(
    feature_id: str = Field(description="Feature ID"),
    criteria: list[str] = Field(description="List of acceptance criteria to add"),
) -> dict:
    """Add acceptance criteria to a feature."""
    return store.add_acceptance_criteria(feature_id, criteria)


# ════════════════════════════════════════════════════════════════════════════
# TASK tools — discrete work items assigned to a repo-scoped agent role
# ════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_task(
    task_id: str = Field(description="Unique task ID, e.g. task-fe-001"),
    feature_id: str = Field(description="Parent feature ID"),
    title: str = Field(description="Short task title"),
    description: str = Field(
        description="Full task description — must be actionable without additional context"
    ),
    owner_role: Literal["frontend", "backend", "orchestrator", "test_e2e"] = Field(
        description="Which agent role owns this task"
    ),
    dependencies: list[str] = Field(
        default_factory=list,
        description="Task IDs that must be completed before this task can start",
    ),
    linked_case_id: str | None = Field(
        default=None,
        description="Optional case ID this task is associated with",
    ),
) -> dict:
    """
    Create a task within a feature.

    Tasks are the atomic unit of work dispatched to repo-scoped agents.
    A task with unsatisfied dependencies will not be offered to agents via
    get_next_task until all dependency tasks are completed.
    """
    return store.create_task(
        task_id=task_id,
        feature_id=feature_id,
        title=title,
        description=description,
        owner_role=owner_role,
        dependencies=dependencies,
        linked_case_id=linked_case_id,
    )


@mcp.tool()
def get_task(task_id: str = Field(description="Task ID")) -> dict:
    """Get a single task's current state."""
    return store.get_task(task_id)


@mcp.tool()
def list_tasks(
    feature_id: str | None = Field(
        default=None,
        description="Filter by feature ID. Omit to list all tasks.",
    ),
) -> list[dict]:
    """List tasks, optionally scoped to a feature."""
    return store.list_tasks(feature_id=feature_id)


@mcp.tool()
def list_tasks_for_feature(
    feature_id: str = Field(description="Feature ID"),
) -> list[dict]:
    """List all tasks for a specific feature."""
    return store.list_tasks(feature_id=feature_id)


@mcp.tool()
def update_task_status(
    task_id: str = Field(description="Task ID"),
    status: Literal[
        "pending",
        "claimed",
        "in_progress",
        "blocked",
        "completed",
        "failed",
        "cancelled",
    ] = Field(description="New task status"),
    result_summary: str | None = Field(
        default=None,
        description="Required when completing or failing a task. Summarize what was done or what failed.",
    ),
) -> dict:
    """
    Update a task's status.

    IMPORTANT: When setting status='completed', provide result_summary.
    This triggers the orchestrator to automatically queue the next wave of tasks
    whose dependencies are now satisfied — no manual intervention needed.
    """
    fields: dict[str, Any] = {"status": status}
    if result_summary is not None:
        fields["result_summary"] = result_summary
    if status == "completed":
        from store import utc_now_iso
        fields["completed_at"] = utc_now_iso()
    elif status in ("in_progress", "claimed"):
        from store import utc_now_iso
        fields["claimed_at"] = utc_now_iso()

    store.update_task(task_id, **fields)
    # Trigger orchestrator — this is the heart of the automation
    return coordinator.on_task_status_changed(task_id)


@mcp.tool()
def add_task_dependency(
    task_id: str = Field(description="Task that depends on another"),
    depends_on_task_id: str = Field(description="Task that must complete first"),
) -> dict:
    """Add a dependency between tasks."""
    task = store.get_task(task_id)
    deps = list(set(task.get("dependencies", []) + [depends_on_task_id]))
    return store.update_task(task_id, dependencies=deps)


@mcp.tool()
def assign_task_owner(
    task_id: str = Field(description="Task ID"),
    owner_role: Literal["frontend", "backend", "orchestrator", "test_e2e"] = Field(
        description="New owner role"
    ),
) -> dict:
    """Reassign a task to a different agent role."""
    return store.update_task(task_id, owner_role=owner_role)


@mcp.tool()
def get_next_task(
    owner_role: Literal["frontend", "backend", "orchestrator", "test_e2e"] = Field(
        description="The calling agent's role"
    ),
    feature_id: str | None = Field(
        default=None,
        description="Limit search to a specific feature. Omit to search all features.",
    ),
) -> dict | None:
    """
    Get the next available task for an agent role.

    Returns the task and automatically claims it (status → 'claimed') so no
    two agents pick up the same task. Returns null if no work is available.

    Agents should call this at the start of each work cycle and after completing
    any task. No manual polling or message-checking is needed.
    """
    task = store.get_next_available_task(owner_role=owner_role, feature_id=feature_id)
    if task is None:
        return None
    # Fire the claimed event
    store.append_event(task["feature_id"], "task_claimed", {"task_id": task["task_id"], "owner_role": owner_role})
    return task


# ════════════════════════════════════════════════════════════════════════════
# CONTRACT tools — shared interface definitions between frontend and backend
# ════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_contract(
    contract_id: str = Field(description="Unique contract ID, e.g. contract-user-api-v1"),
    feature_id: str = Field(description="Parent feature ID"),
    title: str = Field(description="Contract title"),
    description: str = Field(description="What this contract specifies"),
    contract_type: Literal["api", "payload", "schema", "data_model", "other"] = Field(
        description="Type of contract"
    ),
    definition: dict = Field(
        description="The contract definition — endpoint paths, JSON schema, field types, etc."
    ),
) -> dict:
    """
    Create a shared contract (API spec, payload schema, data model).

    Contracts are the source of truth for interfaces between frontend and backend.
    Both agents should check contracts before implementing to avoid divergence.
    """
    return store.create_contract(
        contract_id=contract_id,
        feature_id=feature_id,
        title=title,
        description=description,
        contract_type=contract_type,
        definition=definition,
    )


@mcp.tool()
def get_contract(contract_id: str = Field(description="Contract ID")) -> dict:
    """Get a contract definition."""
    return store.get_contract(contract_id)


@mcp.tool()
def update_contract(
    contract_id: str = Field(description="Contract ID"),
    definition: dict = Field(description="Updated contract definition"),
    version: str | None = Field(default=None, description="New version string, e.g. '1.1'"),
) -> dict:
    """Update a contract definition. Increment version to signal breaking changes."""
    return store.update_contract(contract_id=contract_id, definition=definition, version=version)


@mcp.tool()
def list_contracts(
    feature_id: str | None = Field(
        default=None,
        description="Filter by feature ID. Omit to list all contracts.",
    ),
) -> list[dict]:
    """List contracts, optionally scoped to a feature."""
    return store.list_contracts(feature_id=feature_id)


# ════════════════════════════════════════════════════════════════════════════
# ARTIFACT tools — evidence of work produced by agents
# ════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_artifact(
    artifact_id: str = Field(description="Unique artifact ID, e.g. artifact-fe-login-test-001"),
    task_id: str = Field(description="Task this artifact belongs to"),
    feature_id: str = Field(description="Feature this artifact belongs to"),
    artifact_type: Literal[
        "file_reference",
        "payload",
        "log",
        "test",
        "validation_output",
        "other",
    ] = Field(description="Artifact type"),
    title: str = Field(description="Artifact title"),
    content: str = Field(
        description="Artifact content — file path, JSON payload, log snippet, test output, etc."
    ),
    created_by: Literal["frontend", "backend", "orchestrator", "test_e2e"] = Field(
        description="Agent role that produced this artifact"
    ),
) -> dict:
    """
    Record an artifact produced during task work.

    Artifacts are the evidence trail. Never say 'done' without posting artifacts
    that prove the work was completed correctly.
    """
    return store.create_artifact(
        artifact_id=artifact_id,
        task_id=task_id,
        feature_id=feature_id,
        artifact_type=artifact_type,
        title=title,
        content=content,
        created_by=created_by,
    )


@mcp.tool()
def list_artifacts_for_task(task_id: str = Field(description="Task ID")) -> list[dict]:
    """List all artifacts produced for a task."""
    return store.list_artifacts_for_task(task_id)


@mcp.tool()
def list_artifacts_for_feature(feature_id: str = Field(description="Feature ID")) -> list[dict]:
    """List all artifacts produced for a feature."""
    return store.list_artifacts_for_feature(feature_id)


# ════════════════════════════════════════════════════════════════════════════
# DECISION tools — explicit architectural / design choices
# ════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def create_decision(
    decision_id: str = Field(description="Unique decision ID, e.g. decision-auth-strategy-001"),
    feature_id: str = Field(description="Feature this decision applies to"),
    title: str = Field(description="Decision title"),
    context: str = Field(description="What problem or question prompted this decision"),
    decision: str = Field(description="The decision that was made"),
    rationale: str = Field(description="Why this decision was made"),
    alternatives: list[str] = Field(
        default_factory=list,
        description="Alternatives that were considered and rejected",
    ),
    made_by: Literal["frontend", "backend", "orchestrator", "test_e2e"] = Field(
        description="Agent role that made this decision"
    ),
) -> dict:
    """
    Record an explicit architectural or design decision.

    Decisions prevent the same ground from being re-debated. Any agent can log
    a decision; the orchestrator can require approval before proceeding.
    """
    return store.create_decision(
        decision_id=decision_id,
        feature_id=feature_id,
        title=title,
        context=context,
        decision=decision,
        rationale=rationale,
        alternatives=alternatives,
        made_by=made_by,
    )


@mcp.tool()
def list_decisions_for_feature(feature_id: str = Field(description="Feature ID")) -> list[dict]:
    """List all decisions recorded for a feature."""
    return store.list_decisions_for_feature(feature_id)


# ════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION tools — the control plane
# ════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def dispatch_feature(
    feature_id: str = Field(description="Feature ID to start executing"),
) -> dict:
    """
    Start executing a feature.

    Transitions the feature from 'created'/'planning' to active execution.
    Automatically identifies the first wave of tasks (those with no dependencies)
    and makes them available for agents to claim via get_next_task().

    Call this once after creating a feature and all its tasks. The system will
    then progress the feature autonomously as agents complete work.
    """
    return coordinator.dispatch_feature(feature_id)


@mcp.tool()
def advance_feature(
    feature_id: str = Field(description="Feature ID"),
) -> dict:
    """
    Manually trigger the orchestrator to re-evaluate a feature's state.

    Normally called automatically when tasks change status. Use this to
    unblock a feature after resolving an external dependency or recovering
    from a blocked state.
    """
    return coordinator.advance(feature_id)


@mcp.tool()
def process_events(
    feature_id: str = Field(description="Feature ID"),
) -> dict:
    """
    Get the current state of a feature including recent events, task summary,
    and next-action hints.

    Use this to get a full situational picture without polling individual endpoints.
    """
    return coordinator.process_events(feature_id)


@mcp.tool()
def block_feature(
    feature_id: str = Field(description="Feature ID to block"),
    reason: str = Field(description="Why the feature is blocked"),
) -> dict:
    """
    Mark a feature as blocked with an explicit reason.

    Use when an external dependency, missing information, or unresolvable conflict
    prevents progress. Call advance_feature() once the blocker is resolved.
    """
    return coordinator.block_feature(feature_id, reason)


@mcp.tool()
def await_human_input(
    feature_id: str = Field(description="Feature ID"),
    question: str = Field(description="The specific question requiring human input"),
) -> dict:
    """
    Pause a feature and request human input.

    The feature status transitions to 'awaiting_human_input'. Use
    provide_human_input() to resume. The system will re-run advance() after
    the answer is received.
    """
    return coordinator.await_human_input(feature_id, question)


@mcp.tool()
def provide_human_input(
    feature_id: str = Field(description="Feature ID"),
    answer: str = Field(description="The human's answer to the pending question"),
) -> dict:
    """
    Provide an answer to a pending human-input request.

    Resumes the feature and triggers advance() so the orchestrator can
    continue dispatching work.
    """
    return coordinator.receive_human_input(feature_id, answer)


@mcp.tool()
def mark_feature_complete(
    feature_id: str = Field(description="Feature ID to mark as resolved"),
) -> dict:
    """
    Force-mark a feature as resolved.

    Use when the orchestrator determines all required work is done and all
    acceptance criteria are met. Prefer letting the system auto-resolve via
    task completion over calling this manually.
    """
    return coordinator.mark_feature_complete(feature_id)


@mcp.tool()
def get_feature_summary(
    feature_id: str = Field(description="Feature ID"),
) -> str:
    """
    Export a full markdown summary of a feature including tasks, contracts,
    artifacts, and decisions.
    """
    feature = store.get_feature(feature_id)
    tasks = store.list_tasks(feature_id=feature_id)
    contracts = store.list_contracts(feature_id=feature_id)
    artifacts = store.list_artifacts_for_feature(feature_id)
    decisions = store.list_decisions_for_feature(feature_id)
    events = store.get_events(feature_id)

    lines: list[str] = [
        f"# Feature: {feature['title']}",
        "",
        f"**ID:** {feature['feature_id']}",
        f"**Status:** {feature['status']}",
        f"**Created:** {feature['created_at']}",
        f"**Updated:** {feature['updated_at']}",
        "",
        "## Description",
        "",
        feature["description"],
        "",
    ]

    if feature.get("acceptance_criteria"):
        lines.extend(["## Acceptance Criteria", ""])
        for c in feature["acceptance_criteria"]:
            lines.append(f"- {c}")
        lines.append("")

    if feature.get("linked_case_ids"):
        lines.extend(["## Linked Cases", ""])
        for c in feature["linked_case_ids"]:
            lines.append(f"- {c}")
        lines.append("")

    if feature.get("blocking_reason"):
        lines.extend(["## Blocking Reason", "", feature["blocking_reason"], ""])

    if tasks:
        lines.extend(["## Tasks", ""])
        for t in tasks:
            deps = ", ".join(t.get("dependencies", [])) or "none"
            lines.append(
                f"- **[{t['status'].upper()}]** `{t['task_id']}` ({t['owner_role']}) — {t['title']} _(deps: {deps})_"
            )
            if t.get("result_summary"):
                lines.append(f"  - Result: {t['result_summary']}")
        lines.append("")

    if contracts:
        lines.extend(["## Contracts", ""])
        for c in contracts:
            lines.append(f"- `{c['contract_id']}` ({c['contract_type']}) v{c['version']} — {c['title']}")
        lines.append("")

    if decisions:
        lines.extend(["## Decisions", ""])
        for d in decisions:
            lines.append(f"- **{d['title']}** ({d['made_by']}): {d['decision']}")
        lines.append("")

    if artifacts:
        lines.extend(["## Artifacts", ""])
        for a in artifacts:
            lines.append(f"- `{a['artifact_id']}` ({a['artifact_type']}) — {a['title']} by {a['created_by']}")
        lines.append("")

    if events:
        lines.extend(["## Event Log (last 20)", ""])
        for e in events[-20:]:
            lines.append(f"- `{e['timestamp']}` **{e['event_type']}** {e.get('payload', {})}")
        lines.append("")

    summary = "\n".join(lines).strip() + "\n"

    # Persist alongside feature state
    summary_path = store._feature_dir(feature_id) / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    return summary


if __name__ == "__main__":
    mcp.run()
