from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parent.parent
python_bin = root / ".venv" / "bin" / "python"
server_script = root / "bridge" / "agent_bridge_mcp.py"

config = {
    "mcpServers": {
        "agent-bridge": {
            "command": str(python_bin),
            "args": [str(server_script)],
        }
    }
}

print(json.dumps(config, indent=2))
