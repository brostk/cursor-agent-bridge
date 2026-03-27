from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

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


@dataclass
class BridgeStore:
    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

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

    def create_case(self, case_id: str, title: str, problem: str) -> dict[str, Any]:
        state = {
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
        self.state_path(case_id).write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    def get_case(self, case_id: str) -> dict[str, Any]:
        p = self.state_path(case_id)
        if not p.exists():
            raise FileNotFoundError(f"Case '{case_id}' not found")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_cases(self) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        for child in sorted(self.root.iterdir()):
            if child.is_dir():
                state_file = child / "state.json"
                if state_file.exists():
                    cases.append(json.loads(state_file.read_text(encoding="utf-8")))
        return cases

    def update_case(self, case_id: str, **fields: Any) -> dict[str, Any]:
        state = self.get_case(case_id)
        state.update(fields)
        state["updated_at"] = utc_now_iso()
        self.state_path(case_id).write_text(json.dumps(state, indent=2), encoding="utf-8")
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
        with self.messages_path(case_id).open("a", encoding="utf-8") as f:
            f.write(json.dumps(message) + "\n")
        self.update_case(case_id, status="investigating")
        return message

    def get_messages(self, case_id: str, agent: str | None = None) -> list[dict[str, Any]]:
        _ = self.get_case(case_id)
        path = self.messages_path(case_id)
        if not path.exists():
            return []
        messages: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                msg = json.loads(line)
                if agent is None:
                    messages.append(msg)
                else:
                    if msg["to_agent"] in (agent, "all") or msg["from_agent"] == agent:
                        messages.append(msg)
        return messages

    def resolve_case(self, case_id: str, root_cause: str, proposed_fix: str, validation_steps: list[str]) -> dict[str, Any]:
        state = self.update_case(
            case_id,
            status="resolved",
            root_cause=root_cause,
            proposed_fix=proposed_fix,
            validation_steps=validation_steps,
        )
        return state

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
            lines.extend([
                "## Root cause",
                "",
                state["root_cause"],
                "",
            ])

        if state.get("proposed_fix"):
            lines.extend([
                "## Proposed fix",
                "",
                state["proposed_fix"],
                "",
            ])

        if state.get("validation_steps"):
            lines.append("## Validation steps")
            lines.append("")
            for step in state["validation_steps"]:
                lines.append(f"- {step}")
            lines.append("")

        lines.extend(["## Message log", ""])
        for msg in messages:
            lines.append(f"### {msg['timestamp']} · {msg['from_agent']} -> {msg['to_agent']} · {msg['type']}")
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
