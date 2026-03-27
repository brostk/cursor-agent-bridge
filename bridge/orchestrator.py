"""
Coordinator / Case Runner

This module implements the orchestration layer. It is intentionally stateless —
all persistence flows through BridgeStore. The Coordinator is called by MCP tool
handlers after any state-mutating operation so that features progress automatically
without human intervention.

Orchestration contract
─────────────────────
1. An agent claims a task with get_next_task(owner_role, feature_id).
2. The agent does its work, then calls update_task_status(task_id, "completed", result_summary).
3. update_task_status calls coordinator.on_task_status_changed(task_id).
4. The coordinator scans for newly unblocked tasks, queues them (by leaving them as
   "pending" with satisfied deps), and updates the feature status.
5. The next agent to call get_next_task will pick up the newly available work.

This gives event-driven progression without requiring a background thread.
If you add a background loop later, just call coordinator.advance(feature_id)
on a timer and the logic is identical.
"""

from __future__ import annotations

from typing import Any

from store import BridgeStore


class Coordinator:
    def __init__(self, store: BridgeStore) -> None:
        self.store = store

    # ── public API ────────────────────────────────────────────────────────────

    def dispatch_feature(self, feature_id: str) -> dict[str, Any]:
        """
        Start executing a feature.
        Transitions status from 'created'/'planning' → 'dispatching' → 'in_progress'.
        Immediately runs advance() to queue the first wave of tasks.
        """
        feature = self.store.get_feature(feature_id)
        if feature["status"] in ("resolved", "failed"):
            return self._status_response(feature_id, "already terminal")

        self.store.update_feature(feature_id, status="dispatching")
        self.store.append_event(feature_id, "feature_dispatched", {"feature_id": feature_id})
        return self.advance(feature_id)

    def advance(self, feature_id: str) -> dict[str, Any]:
        """
        Core orchestration step. Call this after any state change.

        - Identifies tasks whose dependencies are now fully satisfied.
        - Detects completion, failures, or blocks.
        - Updates feature status accordingly.
        - Returns a summary dict suitable for returning from an MCP tool.
        """
        feature = self.store.get_feature(feature_id)

        # Terminal states — nothing more to do
        if feature["status"] in ("resolved", "failed", "blocked", "awaiting_human_input"):
            return self._status_response(feature_id, "feature is in a terminal or waiting state")

        tasks = self.store.list_tasks(feature_id=feature_id)

        if not tasks:
            # No tasks defined yet — stay in planning
            self.store.update_feature(feature_id, status="planning")
            return self._status_response(feature_id, "no tasks defined; add tasks then call dispatch_feature")

        by_status: dict[str, list[dict[str, Any]]] = {}
        for t in tasks:
            by_status.setdefault(t["status"], []).append(t)

        completed_ids = {t["task_id"] for t in by_status.get("completed", [])}
        failed_tasks = by_status.get("failed", [])
        pending_tasks = by_status.get("pending", [])
        active_tasks = by_status.get("in_progress", []) + by_status.get("claimed", [])

        # Any failure fails the feature
        if failed_tasks:
            self.store.update_feature(feature_id, status="failed")
            self.store.append_event(
                feature_id,
                "feature_failed",
                {"failed_task_ids": [t["task_id"] for t in failed_tasks]},
            )
            return {
                "feature_id": feature_id,
                "status": "failed",
                "failed_tasks": [t["task_id"] for t in failed_tasks],
                "message": "Feature failed due to task failures. Inspect failed tasks.",
            }

        # Find pending tasks whose deps are now satisfied
        newly_unblocked = [
            t for t in pending_tasks
            if set(t.get("dependencies", [])).issubset(completed_ids)
        ]

        # All tasks complete?
        if not pending_tasks and not active_tasks:
            self.store.update_feature(feature_id, status="resolved")
            self.store.append_event(feature_id, "feature_resolved", {})
            return {
                "feature_id": feature_id,
                "status": "resolved",
                "message": "All tasks complete. Feature resolved.",
                "completed_task_count": len(completed_ids),
            }

        # Update to in_progress
        self.store.update_feature(feature_id, status="in_progress")

        if newly_unblocked:
            self.store.append_event(
                feature_id,
                "tasks_queued",
                {
                    "task_ids": [t["task_id"] for t in newly_unblocked],
                    "owner_roles": list({t["owner_role"] for t in newly_unblocked}),
                },
            )

        return {
            "feature_id": feature_id,
            "status": "in_progress",
            "newly_available_tasks": [
                {"task_id": t["task_id"], "owner_role": t["owner_role"], "title": t["title"]}
                for t in newly_unblocked
            ],
            "active_task_count": len(active_tasks),
            "pending_task_count": len(pending_tasks) - len(newly_unblocked),
            "completed_task_count": len(completed_ids),
            "message": (
                f"{len(newly_unblocked)} task(s) now available. "
                f"Agents should call get_next_task(owner_role) to pick them up."
                if newly_unblocked
                else "Waiting for in-progress tasks to complete."
            ),
        }

    def on_task_status_changed(self, task_id: str) -> dict[str, Any]:
        """
        Called automatically when a task's status changes.
        Triggers advance() on the parent feature so the next wave of work is queued.
        """
        task = self.store.get_task(task_id)
        feature_id = task["feature_id"]

        status = task["status"]

        if status == "completed":
            self.store.append_event(
                feature_id,
                "task_completed",
                {"task_id": task_id, "result_summary": task.get("result_summary")},
            )
        elif status == "failed":
            self.store.append_event(
                feature_id,
                "task_failed",
                {"task_id": task_id},
            )
        elif status == "blocked":
            self.store.append_event(
                feature_id,
                "task_blocked",
                {"task_id": task_id},
            )
        elif status == "in_progress":
            self.store.append_event(
                feature_id,
                "task_claimed",
                {"task_id": task_id},
            )

        return self.advance(feature_id)

    def process_events(self, feature_id: str) -> dict[str, Any]:
        """
        Return current feature state, task summary, and recent events.
        Designed to give any agent a complete situational picture.
        """
        feature = self.store.get_feature(feature_id)
        tasks = self.store.list_tasks(feature_id=feature_id)
        events = self.store.get_events(feature_id)

        task_summary: dict[str, list[str]] = {}
        for t in tasks:
            task_summary.setdefault(t["status"], []).append(t["task_id"])

        return {
            "feature": feature,
            "task_summary": task_summary,
            "recent_events": events[-25:],
            "next_actions": self._next_action_hints(feature, tasks),
        }

    def block_feature(self, feature_id: str, reason: str) -> dict[str, Any]:
        state = self.store.update_feature(feature_id, status="blocked", blocking_reason=reason)
        self.store.append_event(feature_id, "feature_blocked", {"reason": reason})
        return state

    def await_human_input(self, feature_id: str, question: str) -> dict[str, Any]:
        state = self.store.update_feature(
            feature_id,
            status="awaiting_human_input",
            human_input_question=question,
        )
        self.store.append_event(feature_id, "awaiting_human_input", {"question": question})
        return state

    def receive_human_input(self, feature_id: str, answer: str) -> dict[str, Any]:
        self.store.update_feature(
            feature_id,
            status="in_progress",
            human_input_question=None,
            blocking_reason=None,
        )
        self.store.append_event(feature_id, "human_input_received", {"answer": answer})
        return self.advance(feature_id)

    def mark_feature_complete(self, feature_id: str) -> dict[str, Any]:
        state = self.store.update_feature(feature_id, status="resolved")
        self.store.append_event(feature_id, "feature_resolved", {"forced": True})
        return state

    # ── internal helpers ──────────────────────────────────────────────────────

    def _status_response(self, feature_id: str, message: str) -> dict[str, Any]:
        feature = self.store.get_feature(feature_id)
        return {"feature_id": feature_id, "status": feature["status"], "message": message}

    def _next_action_hints(
        self,
        feature: dict[str, Any],
        tasks: list[dict[str, Any]],
    ) -> list[str]:
        hints: list[str] = []
        status = feature["status"]

        if status == "created":
            hints.append("Call dispatch_feature(feature_id) to begin execution.")
        elif status == "planning":
            hints.append("Add tasks with create_task(), then call dispatch_feature(feature_id).")
        elif status == "in_progress":
            roles_needed = {
                t["owner_role"]
                for t in tasks
                if t["status"] == "pending"
                and set(t.get("dependencies", [])).issubset(
                    {t2["task_id"] for t2 in tasks if t2["status"] == "completed"}
                )
            }
            for role in sorted(roles_needed):
                hints.append(f"Call get_next_task(owner_role='{role}') to claim available work.")
        elif status == "blocked":
            hints.append(f"Feature blocked: {feature.get('blocking_reason')}. Resolve blocker then call advance_feature(feature_id).")
        elif status == "awaiting_human_input":
            hints.append(f"Human input needed: {feature.get('human_input_question')}. Call provide_human_input(feature_id, answer) when ready.")
        elif status == "resolved":
            hints.append("Feature is resolved. Call export_feature_summary(feature_id) to generate a report.")
        elif status == "failed":
            hints.append("Feature failed. Inspect failed tasks, fix issues, and re-dispatch.")

        return hints
