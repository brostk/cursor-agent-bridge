# Agent Bridge — Multi-Agent Coordination for Cursor

A local MCP server that lets multiple Cursor agents — each working in their own repo — coordinate on a bug investigation or feature delivery without you relaying messages between them.

---

## What you actually do

For a bug investigation, you write **three prompts** — then walk away:

**1. In any Cursor window (your orchestrator):**
> Investigate why the 1010d checkout form is returning a 502. The frontend is sending `billingAddress.country: "United States"` but the backend appears to expect an ISO-2 code.

The orchestrator creates the case, confirms the case ID back to you, and **immediately begins monitoring**. It will report status updates to you in its window as the agents work — no re-prompting needed.

**2. In your frontend repo window:**
> Pick up case `checkout-502-001` as the frontend investigator and start tracing how the country field is built and submitted.

**3. In your backend repo window:**
> Pick up case `checkout-502-001` as the backend investigator and start tracing how the country value is validated and forwarded to the upstream service.

From here, watch the **orchestrator window**. It reads both agents' findings, posts coordinating messages to direct the agents when needed, and gives you a plain-English status update after each cycle. When the case is resolved, it tells you.

You don't re-prompt. You don't check the other windows. You don't relay messages. The orchestrator handles it.

---

## The orchestrator window is your dashboard

Once you've given those three prompts, the orchestrator window is the only one you need to watch. It will:

- Summarize new findings from each agent as they come in
- Spot contradictions and post clarifying questions to the right agent
- Nudge agents that have gone quiet
- Tell you the leading hypothesis and how close to resolution things look
- Report when the case is done, with root cause, fix, and validation steps

---

## How it works (background)

The MCP server is a shared ledger that all agents read and write. When an agent posts a finding, the other agents see it on their next read. When a backend task completes during delivery work, the system automatically makes the dependent frontend task available.

The orchestrator is just a Cursor agent with a prompt that instructs it to run a monitoring loop after setup. It uses the same MCP tools as the other agents — reading messages, posting coordination notes, checking case status — on a continuous cycle until the work is done.

There are two workflows:

**Debugging (cases)** — for investigation. Agents post findings, hypotheses, and evidence. The orchestrator coordinates. You resolve the case when root cause and fix are clear.

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

Paste the output into your Cursor MCP settings (`Cursor → Settings → MCP`). Do this for every Cursor window that needs access — typically the orchestrator window plus one per repo.

---

## Role prompts

Paste these into your agent's system prompt or prepend to your first message:

| Window | Prompt file |
|---|---|
| Orchestrator (any window) | `prompts/orchestrator.md` |
| Frontend repo — debugging | `prompts/frontend_investigator.md` |
| Backend repo — debugging | `prompts/backend_investigator.md` |
| Frontend repo — delivery | `prompts/frontend_implementer.md` |
| Backend repo — delivery | `prompts/backend_implementer.md` |
| Test / E2E | `prompts/test_e2e_agent.md` |

---

## Debugging workflow

### You do

1. **Orchestrator window:** Ask it to investigate the bug. It creates the case and starts monitoring automatically.
2. **Frontend window:** Tell the frontend investigator which case to join and where to start.
3. **Backend window:** Tell the backend investigator which case to join and where to start.
4. Watch the orchestrator window for updates.

### What the orchestrator does automatically

- Reads new findings from both agents after each cycle (~90 seconds)
- Posts coordinating messages to direct agents when needed
- Reports status to you in plain English
- Tells you when the case is resolved

### You do at the end

Nothing — the orchestrator reports completion. Optionally ask it to export a summary.

See `examples/debugging_workflow.md` for a concrete walkthrough.

---

## Delivery workflow

### You do

1. **Orchestrator window:** Ask it to create and dispatch a feature. It plans the task graph and starts monitoring automatically.
2. **Backend window:** Tell the backend implementer to pick up their next task.
3. **Frontend window:** Tell the frontend implementer to pick up their next task.
4. Watch the orchestrator window for updates.

### What happens automatically

- Backend completes → system unlocks frontend task
- Frontend completes → system unlocks E2E task
- All tasks complete → feature resolves
- Orchestrator reports each transition to you

See `examples/delivery_workflow.md` for a concrete walkthrough.

---

## Checking in

You can ask the orchestrator at any point:

> What's the current status?

It will read the latest state and give you a summary. But if the orchestrator is running its monitoring loop, you shouldn't need to ask — it's already reporting to you.

---

## Files in this repo

```
bridge/
  agent_bridge_mcp.py    — MCP server entrypoint (44 tools)
  store.py               — filesystem persistence
  orchestrator.py        — task sequencing logic
  models.py              — data models

prompts/
  orchestrator.md              — orchestrator role + monitoring loop
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

**An agent stopped after completing work and is waiting for a prompt**
This means the role prompt wasn't attached or wasn't followed. Each prompt contains an explicit loop instruction — make sure it's included at the start of the conversation (as a system prompt or prepended to the first message). If an agent stops mid-investigation, tell it: "Resume your loop for case X" — it will pick back up. Going forward, confirm the prompt is in place before starting.

**Orchestrator stopped monitoring**
Cursor agents can time out on long-running loops. If the orchestrator window goes idle, just tell it: "Resume monitoring case X."

**Frontend agent isn't seeing backend findings**
Both agents must have the MCP server configured and use the same case ID. Ask the frontend agent: "Read all messages for case X."

**A task never becomes available to an agent**
The task has a dependency that isn't completed yet. Ask the orchestrator: "Show me all tasks for feature X and their current status."

**Feature stuck, nothing is progressing**
Ask the orchestrator: "Show me the event log and next actions for feature X." The response includes explicit hints on what needs to happen next.
