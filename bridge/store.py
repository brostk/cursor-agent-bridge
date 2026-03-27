from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from models import (
    AgentRole,
    ArtifactType,
    ContractType,
    EventType,
    FeatureStatus,
    TaskStatus,
)

MessageType = Literal[
    "question",
    "finding",
    "hypothesis",
    "request_for_repro",
    "proposed_fix",
    "resolved",
    "blocked",
]

AgentName = Literal["frontend", "backend", "orchestrator"]
RecipientName = Literal["frontend", "backend", "all"]
CaseStatus = Literal["open", "investigating", "resolved", "blocked"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def short_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class BridgeStore:
    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._features_dir.mkdir(parents=True, exist_ok=True)
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        self._contracts_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._decisions_dir.mkdir(parents=True, exist_ok=True)

    # ── path helpers ────────────────────────────────────────────────────────

    @property
    def _features_dir(self) -> Path:
        return self.root / "_features"

    @property
    def _tasks_dir(self) -> Path:
        return self.root / "_tasks"

    @property
    def _contracts_dir(self) -> Path:
        return self.root / "_contracts"

    @property
    def _artifacts_dir(self) -> Path:
        return self.root / "_artifacts"

    @property
    def _decisions_dir(self) -> Path:
        return self.root / "_decisions"

    def case_dir(self, case_id: str) -> Path:
        d = self.root / case_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def state_path(self, case_id: str) -> Path:
        return self.case_dir(case_id) / "state.json"

    def messages_path(self, case_id: str) -> Path:
        return self.case_dir(case_id) / "messages.jsonl"

    def summary_path(self, case_id: str) -> Path:
        return self.case_dir(case_id) / "summary.md"

    def _feature_dir(self, feature_id: str) -> Path:
        d = self._features_dir / feature_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _feature_state_path(self, feature_id: str) -> Path:
        return self._feature_dir(feature_id) / "state.json"

    def _feature_events_path(self, feature_id: str) -> Path:
        return self._feature_dir(feature_id) / "events.jsonl"

    def _task_path(self, task_id: str) -> Path:
        return self._tasks_dir / f"{task_id}.json"

    def _contract_path(self, contract_id: str) -> Path:
        return self._contracts_dir / f"{contract_id}.json"

    def _artifact_path(self, artifact_id: str) -> Path:
        return self._artifacts_dir / f"{artifact_id}.json"

    def _decision_path(self, decision_id: str) -> Path:
        return self._decisions_dir / f"{decision_id}.json"

    # ── internal helpers ─────────────────────────────────────────────────────

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _append_jsonl(self, path: Path, record: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        out: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    # ════════════════════════════════════════════════════════════════════════
    # CASE operations (unchanged for backward compat)
    # ════════════════════════════════════════════════════════════════════════

    def create_case(self, case_id: str, title: str, problem: str) -> dict[str, Any]:
        state: dict[str, Any] = {
            "case_id": case_id,
            "title": title,
            "problem": problem,
            "status": "open",
            "root_cause": None,
            "proposed_fix": None,
            "validation_steps": [],
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        self._write_json(self.state_path(case_id), state)
        return state

    def get_case(self, case_id: str) -> dict[str, Any]:
        p = self.state_path(case_id)
        if not p.exists():
            raise FileNotFoundError(f"Case '{case_id}' not found")
        return self._read_json(p)

    def list_cases(self) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        for child in sorted(self.root.iterdir()):
            # skip internal dirs that start with _
            if child.is_dir() and not child.name.startswith("_"):
                state_file = child / "state.json"
                if state_file.exists():
                    cases.append(self._read_json(state_file))
        return cases

    def update_case(self, case_id: str, **fields: Any) -> dict[str, Any]:
        state = self.get_case(case_id)
        state.update(fields)
        state["updated_at"] = utc_now_iso()
        self._write_json(self.state_path(case_id), state)
        return state

    def post_message(
        self,
        case_id: str,
        from_agent: str,
        to_agent: str,
        msg_type: str,
        summary: str,
        evidence: list[str] | None = None,
        hypothesis: str | None = None,
        question: str | None = None,
        priority: str = "medium",
    ) -> dict[str, Any]:
        _ = self.get_case(case_id)
        message = {
            "case_id": case_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "type": msg_type,
            "summary": summary,
            "evidence": evidence or [],
            "hypothesis": hypothesis,
            "question": question,
            "priority": priority,
            "timestamp": utc_now_iso(),
        }
        self._append_jsonl(self.messages_path(case_id), message)
        self.update_case(case_id, status="investigating")
        return message

    def get_messages(self, case_id: str, agent: str | None = None) -> list[dict[str, Any]]:
        _ = self.get_case(case_id)
        messages = self._read_jsonl(self.messages_path(case_id))
        if agent is None:
            return messages
        return [
            m for m in messages
            if m["to_agent"] in (agent, "all") or m["from_agent"] == agent
        ]

    def resolve_case(
        self,
        case_id: str,
        root_cause: str,
        proposed_fix: str,
        validation_steps: list[str],
    ) -> dict[str, Any]:
        return self.update_case(
            case_id,
            status="resolved",
            root_cause=root_cause,
            proposed_fix=proposed_fix,
            validation_steps=validation_steps,
        )

    def export_summary(self, case_id: str) -> str:
        state = self.get_case(case_id)
        messages = self.get_messages(case_id)

        lines = [
            f"# Case {state['case_id']}",
            "",
            f"**Title:** {state['title']}",
            "",
            f"**Problem:** {state['problem']}",
            "",
            f"**Status:** {state['status']}",
            "",
        ]

        if state.get("root_cause"):
            lines.extend(["## Root cause", "", state["root_cause"], ""])

        if state.get("proposed_fix"):
            lines.extend(["## Proposed fix", "", state["proposed_fix"], ""])

        if state.get("validation_steps"):
            lines.append("## Validation steps")
            lines.append("")
            for step in state["validation_steps"]:
                lines.append(f"- {step}")
            lines.append("")

        lines.extend(["## Message log", ""])
        for msg in messages:
            lines.append(
                f"### {msg['timestamp']} · {msg['from_agent']} -> {msg['to_agent']} · {msg['type']}"
            )
            lines.append("")
            lines.append(msg["summary"])
            lines.append("")
            if msg.get("evidence"):
                lines.append("Evidence:")
                for item in msg["evidence"]:
                    lines.append(f"- {item}")
                lines.append("")
            if msg.get("hypothesis"):
                lines.append(f"Hypothesis: {msg['hypothesis']}")
                lines.append("")
            if msg.get("question"):
                lines.append(f"Question: {msg['question']}")
                lines.append("")

        summary = "\n".join(lines).strip() + "\n"
        self.summary_path(case_id).write_text(summary, encoding="utf-8")
        return summary

    # ════════════════════════════════════════════════════════════════════════
    # FEATURE operations
    # ════════════════════════════════════════════════════════════════════════

    def create_feature(
        self,
        feature_id: str,
        title: str,
        description: str,
        linked_case_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        state: dict[str, Any] = {
            "feature_id": feature_id,
            "title": title,
            "description": description,
            "status": "created",
            "acceptance_criteria": [],
            "linked_case_ids": linked_case_ids or [],
            "blocking_reason": None,
            "human_input_question": None,
            "created_at": now,
            "updated_at": now,
        }
        self._write_json(self._feature_state_path(feature_id), state)
        self.append_event(feature_id, "feature_created", {"feature_id": feature_id, "title": title})
        return state

    def get_feature(self, feature_id: str) -> dict[str, Any]:
        p = self._feature_state_path(feature_id)
        if not p.exists():
            raise FileNotFoundError(f"Feature '{feature_id}' not found")
        return self._read_json(p)

    def list_features(self) -> list[dict[str, Any]]:
        features: list[dict[str, Any]] = []
        for child in sorted(self._features_dir.iterdir()):
            if child.is_dir():
                p = child / "state.json"
                if p.exists():
                    features.append(self._read_json(p))
        return features

    def update_feature(self, feature_id: str, **fields: Any) -> dict[str, Any]:
        state = self.get_feature(feature_id)
        state.update(fields)
        state["updated_at"] = utc_now_iso()
        self._write_json(self._feature_state_path(feature_id), state)
        return state

    def add_acceptance_criteria(self, feature_id: str, criteria: list[str]) -> dict[str, Any]:
        state = self.get_feature(feature_id)
        existing = set(state.get("acceptance_criteria", []))
        for c in criteria:
            existing.add(c)
        return self.update_feature(feature_id, acceptance_criteria=sorted(existing))

    # ════════════════════════════════════════════════════════════════════════
    # TASK operations
    # ════════════════════════════════════════════════════════════════════════

    def create_task(
        self,
        task_id: str,
        feature_id: str,
        title: str,
        description: str,
        owner_role: AgentRole,
        dependencies: list[str] | None = None,
        linked_case_id: str | None = None,
    ) -> dict[str, Any]:
        # validate feature exists
        _ = self.get_feature(feature_id)
        now = utc_now_iso()
        task: dict[str, Any] = {
            "task_id": task_id,
            "feature_id": feature_id,
            "title": title,
            "description": description,
            "owner_role": owner_role,
            "status": "pending",
            "dependencies": dependencies or [],
            "linked_case_id": linked_case_id,
            "created_at": now,
            "updated_at": now,
            "claimed_at": None,
            "completed_at": None,
            "result_summary": None,
        }
        self._write_json(self._task_path(task_id), task)
        self.append_event(feature_id, "task_created", {"task_id": task_id, "owner_role": owner_role})
        return task

    def get_task(self, task_id: str) -> dict[str, Any]:
        p = self._task_path(task_id)
        if not p.exists():
            raise FileNotFoundError(f"Task '{task_id}' not found")
        return self._read_json(p)

    def update_task(self, task_id: str, **fields: Any) -> dict[str, Any]:
        task = self.get_task(task_id)
        task.update(fields)
        task["updated_at"] = utc_now_iso()
        self._write_json(self._task_path(task_id), task)
        return task

    def list_tasks(self, feature_id: str | None = None) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        for p in sorted(self._tasks_dir.glob("*.json")):
            t = self._read_json(p)
            if feature_id is None or t.get("feature_id") == feature_id:
                tasks.append(t)
        return tasks

    def get_next_available_task(
        self,
        owner_role: AgentRole,
        feature_id: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Find the next pending task for owner_role whose dependencies are all completed.
        Claims it atomically by flipping status to 'claimed'.
        Returns None if no task is available.
        """
        all_tasks = self.list_tasks(feature_id=feature_id)
        completed_ids = {t["task_id"] for t in all_tasks if t["status"] == "completed"}

        for task in all_tasks:
            if task["owner_role"] != owner_role:
                continue
            if task["status"] != "pending":
                continue
            deps = set(task.get("dependencies", []))
            if deps.issubset(completed_ids):
                # claim it
                return self.update_task(
                    task["task_id"],
                    status="claimed",
                    claimed_at=utc_now_iso(),
                )
        return None

    # ════════════════════════════════════════════════════════════════════════
    # CONTRACT operations
    # ════════════════════════════════════════════════════════════════════════

    def create_contract(
        self,
        contract_id: str,
        feature_id: str,
        title: str,
        description: str,
        contract_type: ContractType,
        definition: dict[str, Any],
    ) -> dict[str, Any]:
        _ = self.get_feature(feature_id)
        now = utc_now_iso()
        contract: dict[str, Any] = {
            "contract_id": contract_id,
            "feature_id": feature_id,
            "title": title,
            "description": description,
            "contract_type": contract_type,
            "definition": definition,
            "version": "1.0",
            "created_at": now,
            "updated_at": now,
        }
        self._write_json(self._contract_path(contract_id), contract)
        self.append_event(
            feature_id,
            "contract_created",
            {"contract_id": contract_id, "contract_type": contract_type},
        )
        return contract

    def get_contract(self, contract_id: str) -> dict[str, Any]:
        p = self._contract_path(contract_id)
        if not p.exists():
            raise FileNotFoundError(f"Contract '{contract_id}' not found")
        return self._read_json(p)

    def update_contract(
        self,
        contract_id: str,
        definition: dict[str, Any],
        version: str | None = None,
    ) -> dict[str, Any]:
        contract = self.get_contract(contract_id)
        contract["definition"] = definition
        if version:
            contract["version"] = version
        contract["updated_at"] = utc_now_iso()
        self._write_json(self._contract_path(contract_id), contract)
        return contract

    def list_contracts(self, feature_id: str | None = None) -> list[dict[str, Any]]:
        contracts: list[dict[str, Any]] = []
        for p in sorted(self._contracts_dir.glob("*.json")):
            c = self._read_json(p)
            if feature_id is None or c.get("feature_id") == feature_id:
                contracts.append(c)
        return contracts

    # ════════════════════════════════════════════════════════════════════════
    # ARTIFACT operations
    # ════════════════════════════════════════════════════════════════════════

    def create_artifact(
        self,
        artifact_id: str,
        task_id: str,
        feature_id: str,
        artifact_type: ArtifactType,
        title: str,
        content: str,
        created_by: AgentRole,
    ) -> dict[str, Any]:
        artifact: dict[str, Any] = {
            "artifact_id": artifact_id,
            "task_id": task_id,
            "feature_id": feature_id,
            "artifact_type": artifact_type,
            "title": title,
            "content": content,
            "created_by": created_by,
            "created_at": utc_now_iso(),
        }
        self._write_json(self._artifact_path(artifact_id), artifact)
        self.append_event(
            feature_id,
            "artifact_created",
            {"artifact_id": artifact_id, "task_id": task_id, "artifact_type": artifact_type},
        )
        return artifact

    def list_artifacts_for_task(self, task_id: str) -> list[dict[str, Any]]:
        return [
            self._read_json(p)
            for p in sorted(self._artifacts_dir.glob("*.json"))
            if self._read_json(p).get("task_id") == task_id
        ]

    def list_artifacts_for_feature(self, feature_id: str) -> list[dict[str, Any]]:
        return [
            self._read_json(p)
            for p in sorted(self._artifacts_dir.glob("*.json"))
            if self._read_json(p).get("feature_id") == feature_id
        ]

    # ════════════════════════════════════════════════════════════════════════
    # DECISION operations
    # ════════════════════════════════════════════════════════════════════════

    def create_decision(
        self,
        decision_id: str,
        feature_id: str,
        title: str,
        context: str,
        decision: str,
        rationale: str,
        alternatives: list[str],
        made_by: AgentRole,
    ) -> dict[str, Any]:
        _ = self.get_feature(feature_id)
        record: dict[str, Any] = {
            "decision_id": decision_id,
            "feature_id": feature_id,
            "title": title,
            "context": context,
            "decision": decision,
            "rationale": rationale,
            "alternatives": alternatives,
            "made_by": made_by,
            "created_at": utc_now_iso(),
        }
        self._write_json(self._decision_path(decision_id), record)
        self.append_event(feature_id, "decision_created", {"decision_id": decision_id})
        return record

    def list_decisions_for_feature(self, feature_id: str) -> list[dict[str, Any]]:
        return [
            self._read_json(p)
            for p in sorted(self._decisions_dir.glob("*.json"))
            if self._read_json(p).get("feature_id") == feature_id
        ]

    # ════════════════════════════════════════════════════════════════════════
    # EVENT log
    # ════════════════════════════════════════════════════════════════════════

    def append_event(
        self,
        feature_id: str,
        event_type: EventType,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_id": short_id(),
            "feature_id": feature_id,
            "event_type": event_type,
            "payload": payload or {},
            "timestamp": utc_now_iso(),
        }
        self._append_jsonl(self._feature_events_path(feature_id), event)
        return event

    def get_events(self, feature_id: str) -> list[dict[str, Any]]:
        _ = self.get_feature(feature_id)
        return self._read_jsonl(self._feature_events_path(feature_id))
