# Agent Bridge — Multi-Agent Coordination for Cursor

A local MCP server that lets multiple Cursor agents — each working in their own repo — coordinate on a bug investigation or feature delivery without you relaying messages between them.

---

## What you actually do

For a bug investigation, you write **three prompts** — then walk away:

**1. In any Cursor window (your orchestrator):**
> Create a new agent-bridge case to investigate why the 1010d checkout form is returning a 502. The frontend is sending `billingAddress.country: "United States"` but the backend appears to expect an ISO-2 code.

The agent will create the case and tell you the case ID it used (e.g. `checkout-502-001`). Use that ID in the next two prompts.

**2. In your frontend repo window:**
> Pick up case `checkout-502-001` as the frontend investigator and start tracing how the country field is built and submitted.

**3. In your backend repo window:**
> Pick up case `checkout-502-001` as the backend investigator and start tracing how the country value is validated and forwarded to the upstream service.

From here the agents coordinate through the shared MCP server — posting findings, reading each other's evidence, converging on a root cause — without you in the loop. No re-prompting. No "check for updates." No copying messages between windows.

For a feature delivery the flow is the same shape: orchestrator plans and dispatches, then you give the frontend and backend agents one prompt each to start working.

---

## How it works (background)

The MCP server is a shared ledger that all agents read and write. When an agent posts a finding, the other agents see it on their next read. When a backend task completes, the system automatically makes the dependent frontend task available — no human needs to signal "your turn."

There are two workflows:

**Debugging (cases)** — for investigation. Agents post findings, hypotheses, and evidence. You resolve the case when root cause and fix are clear.

**Delivery (features)** — for implementation. The orchestrator creates a task graph with explicit dependencies. Tasks are claimed by agents and sequenced automatically. The feature resolves itself when all tasks are complete.

Cases and features can be linked: the orchestrator can open a feature to track the fix for an investigated case.

---

## Setup

### 1. Install dependencies

```bash
cd cursor-agent-bridge-starter
bash scripts/setup.sh
```

### 2. Start the MCP server

```bash
source .venv/bin/activate
bash scripts/run_mcp.sh
```

Keep this running in a terminal. It persists all shared state to `agent_bridge_data/` as plain JSON files.

### 3. Add the MCP server to Cursor

```bash
source .venv/bin/activate
python scripts/print_mcp_config.py
```

Paste the output into your Cursor MCP settings (`Cursor → Settings → MCP`). Do this for every Cursor window that needs access — typically one per repo plus the orchestrator window.

---

## Role prompts

Paste these into your agent's system prompt or prepend to your first message:

| Window | Prompt file |
|---|---|
| Orchestrator (any window) | `prompts/orchestrator.md` |
| Frontend repo | `prompts/frontend_implementer.md` or `prompts/frontend_investigator.md` |
| Backend repo | `prompts/backend_implementer.md` or `prompts/backend_investigator.md` |
| Test / E2E | `prompts/test_e2e_agent.md` |

Use the `investigator` variants for debugging, `implementer` variants for delivery.

---

## Debugging workflow

### You do

1. **Orchestrator window:** Ask it to create a case describing the bug — case ID, title, problem statement.
2. **Frontend window:** Tell the frontend investigator which case to join and where to start looking.
3. **Backend window:** Tell the backend investigator which case to join and where to start looking.
4. Wait.

### Agents do (automatically)

- Post findings, hypotheses, and questions to the shared case
- Read each other's messages after each meaningful discovery
- Narrow down to a root cause
- One agent posts a proposed fix; another validates it

### You do at the end

- Ask any agent to resolve the case with root cause, fix, and validation steps
- Optionally ask for a summary: `export_case_summary`

See `examples/debugging_workflow.md` for a concrete walkthrough.

---

## Delivery workflow

### You do

1. **Orchestrator window:** Ask it to create a feature, define the acceptance criteria, create the task graph (backend → frontend → test/e2e), and dispatch.
2. **Backend window:** Tell the backend implementer to pick up their next task for this feature.
3. **Frontend window:** Tell the frontend implementer to pick up their next task for this feature.
4. Wait.

### Agents do (automatically)

- Each agent claims its available task
- Backend completes → system automatically unlocks frontend task
- Frontend completes → system automatically unlocks e2e task
- E2e completes → feature auto-resolves

No agent needs to be re-prompted or told "the other agent finished."

### You do at the end

- Nothing, if all tasks complete. Feature status flips to `resolved` automatically.
- If something blocks, the agent will post a blocked status with a specific reason. You resolve the blocker and the orchestrator re-dispatches.

See `examples/delivery_workflow.md` for a concrete walkthrough.

---

## Checking status

From any window, ask the agent:

> What's the current status of case `checkout-502-001`?

> Summarize all tasks for feature `feat-checkout-country-001`.

> Show me the event log for feature `feat-checkout-country-001`.

The agent will call the appropriate MCP tools and return a readable summary. You never need to read raw JSON.

---

## Files in this repo

```
bridge/
  agent_bridge_mcp.py    — MCP server entrypoint (44 tools)
  store.py               — filesystem persistence
  orchestrator.py        — task sequencing logic
  models.py              — data models

prompts/
  orchestrator.md              — orchestrator role
  frontend_investigator.md     — debugging, frontend
  backend_investigator.md      — debugging, backend
  frontend_implementer.md      — delivery, frontend
  backend_implementer.md       — delivery, backend
  test_e2e_agent.md            — validation
  referee.md                   — contradiction resolution

examples/
  debugging_workflow.md        — step-by-step debugging example
  delivery_workflow.md         — step-by-step delivery example
  sample_case.json             — sample case seed data
  sample_feature.json          — sample feature
  sample_tasks.json            — sample task graph
  sample_contract.json         — sample API contract

scripts/
  setup.sh               — create venv and install deps
  run_mcp.sh             — start the MCP server
  print_mcp_config.py    — print Cursor MCP config snippet
  seed_sample_case.sh    — seed the sample case
```

---

## Troubleshooting

**Agent says it can't find the MCP tools**
Make sure the MCP server is running (`bash scripts/run_mcp.sh`) and the config from `print_mcp_config.py` is pasted into Cursor's MCP settings for that window.

**Frontend agent isn't seeing backend findings**
Both agents must have the MCP server configured and use the same case ID. Ask the frontend agent: "Read all messages for case X."

**A task never becomes available to an agent**
The task has a dependency that isn't completed yet. Ask the orchestrator: "Show me all tasks for feature X and their current status."

**Feature stuck, nothing is progressing**
Ask the orchestrator: "Show me the event log and next actions for feature X." The response includes explicit hints on what needs to happen next.
