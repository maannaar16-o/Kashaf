#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / ".ai-handoff" / "TASK_QUEUE.json"
HANDOFF = ROOT / ".ai-handoff" / "HANDOFF.json"

STATUSES = {
    "queued", "in_progress", "ready_for_codex", "changes_requested",
    "approved", "owner_decision_required", "blocked"
}
ACTORS = {"owner", "claude", "codex"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]

def fail(message):
    print(f"ERROR: {message}")
    return 1

def load(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def main():
    errors = []
    for path in (QUEUE, HANDOFF):
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        return fail("; ".join(errors))

    try:
        queue = load(QUEUE)
        handoff = load(HANDOFF)
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"invalid JSON: {exc}")

    tasks = queue.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("TASK_QUEUE.tasks must be a non-empty list")
        tasks = []

    ids = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"task {index} must be an object")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"task {index} has no valid id")
        else:
            ids.append(task_id)
        if task.get("status") not in STATUSES:
            errors.append(f"task {task_id or index} has invalid status")
        if task.get("next_actor") not in ACTORS:
            errors.append(f"task {task_id or index} has invalid next_actor")
        iteration = task.get("iteration")
        maximum = task.get("max_iterations")
        if not isinstance(iteration, int) or iteration < 0:
            errors.append(f"task {task_id or index} has invalid iteration")
        if not isinstance(maximum, int) or maximum < 1:
            errors.append(f"task {task_id or index} has invalid max_iterations")
        if isinstance(iteration, int) and isinstance(maximum, int) and iteration > maximum:
            errors.append(f"task {task_id or index} exceeds max_iterations")

    if len(ids) != len(set(ids)):
        errors.append("task ids must be unique")
    if handoff.get("task_id") not in ids:
        errors.append("HANDOFF.task_id must match a queued task")
    if handoff.get("status") not in STATUSES:
        errors.append("HANDOFF.status is invalid")
    if handoff.get("from_actor") not in ACTORS or handoff.get("to_actor") not in ACTORS:
        errors.append("HANDOFF actors are invalid")

    for field in ("changed_files", "commands_run", "tests", "findings", "blockers", "decisions_needed"):
        if not isinstance(handoff.get(field), list):
            errors.append(f"HANDOFF.{field} must be a list")

    raw = QUEUE.read_text(encoding="utf-8") + HANDOFF.read_text(encoding="utf-8")
    if any(pattern.search(raw) for pattern in SECRET_PATTERNS):
        errors.append("possible secret detected in handoff files")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"PASS: {len(tasks)} task(s); handoff protocol is valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())
