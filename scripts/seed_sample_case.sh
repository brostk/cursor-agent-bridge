#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("bridge").resolve()))
from store import BridgeStore

root = Path("agent_bridge_data")
store = BridgeStore(root)

sample = json.loads(Path("examples/sample_case.json").read_text(encoding="utf-8"))

try:
    existing = store.get_case(sample["case_id"])
    print(f"[ok] case already exists: {existing['case_id']}")
except FileNotFoundError:
    created = store.create_case(
        case_id=sample["case_id"],
        title=sample["title"],
        problem=sample["problem"],
    )
    print(f"[ok] created case: {created['case_id']}")
PY
