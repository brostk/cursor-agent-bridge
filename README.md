# Cursor Agent Bridge Starter

A ready-to-run starter repo for coordinating two Cursor agents on a full-stack bug:
one agent focused on the frontend repo, one agent focused on the backend repo.

This starter is updated for modern Cursor workflows:
- use **Multi-Agents** to run parallel investigators in isolated worktrees
- use **subagent-style role prompts** for frontend, backend, and referee responsibilities
- use a local **MCP server** as the shared case room / evidence ledger
- optionally hand longer runs to **Cloud Agents / Background Agents**
- keep everything structured, so agents exchange evidence instead of vague chat

## Why this shape

Recent Cursor releases added:
- **Multi-Agents**, which can run up to eight agents in parallel in isolated copies of a codebase
- **Subagents**, including custom subagents with separate prompts, context, tools, and models
- **Async subagents**, so the parent can keep working while delegated work continues
- **Skills**, for reusable task-specific workflows
- **Plugins**, which can package skills, subagents, MCP servers, hooks, and rules together
- stronger **MCP** support and easier MCP auth/config flows

This repo takes advantage of that direction by moving the cross-window communication into a local MCP server and giving you reusable prompts/rules you can attach to your agents.

## Repo layout

```text
cursor-agent-bridge-starter/
  README.md
  requirements.txt
  bridge/
    agent_bridge_mcp.py
    store.py
  prompts/
    frontend_investigator.md
    backend_investigator.md
    referee.md
    shared_case_template.md
    parent_orchestrator.md
  scripts/
    setup.sh
    run_mcp.sh
    seed_sample_case.sh
    print_mcp_config.py
  examples/
    sample_case.json
    cursor_multi_agent_message.md
  .cursor/
    rules/
      agent-bridge.mdc
```

## What the MCP server does

The local MCP server is the shared incident room. It exposes tools for:
- creating a case
- posting findings / questions / hypotheses
- polling messages for one agent
- reading current case state
- resolving a case
- exporting a markdown summary

This lets the frontend and backend agents communicate without you relaying messages between chats.

## Quick start

### 1) Set up the environment

```bash
cd cursor-agent-bridge-starter
bash scripts/setup.sh
```

### 2) Start the local MCP server

```bash
source .venv/bin/activate
bash scripts/run_mcp.sh
```

### 3) Print a sample Cursor MCP config snippet

```bash
source .venv/bin/activate
python scripts/print_mcp_config.py
```

That prints a JSON snippet you can adapt into your local Cursor MCP settings.

### 4) Seed the sample bug case

```bash
source .venv/bin/activate
bash scripts/seed_sample_case.sh
```

### 5) In Cursor, create your agents

Recommended setup:
- **Agent A**: frontend investigator, attached to the frontend repo
- **Agent B**: backend investigator, attached to the backend repo
- optional **Agent C**: referee/orchestrator

Use the prompt files in `prompts/` for the role instructions.

### 6) Give the parent/orchestrator a starter message

See `examples/cursor_multi_agent_message.md`.

## Recommended Cursor workflow

### Best path: Multi-Agents + MCP
1. Open one main Cursor conversation in the repo you want as the coordination home.
2. Ask Cursor to spawn two parallel agents:
   - one frontend investigator
   - one backend investigator
3. Tell both to use the Agent Bridge MCP tools for all cross-agent communication.
4. Keep the parent agent in charge of:
   - case creation
   - progress checks
   - contradiction detection
   - final synthesis

### Practical path: two windows + MCP
If you still prefer one window per repo:
1. open frontend repo in one Cursor window
2. open backend repo in another
3. give each the matching prompt from `prompts/`
4. tell each agent to use the MCP tools for all peer communication

## Suggested parent prompt pattern

Use `prompts/parent_orchestrator.md` as the parent instruction, then tell Cursor:

- create a case from the shared case template
- launch or emulate a frontend investigator and a backend investigator
- have both agents post only structured evidence
- require each conclusion to cite code locations, logs, or a reproducible request/response artifact
- do not mark resolved until root cause, fix, and validation steps are explicit

## Message protocol

Supported message types:
- `question`
- `finding`
- `hypothesis`
- `request_for_repro`
- `proposed_fix`
- `resolved`
- `blocked`

Each message includes:
- case id
- from agent
- to agent
- summary
- evidence list
- optional hypothesis
- optional question
- priority
- timestamp

## Example investigation loop

1. frontend agent inspects UI event, request payload, headers, timing
2. backend agent traces route, validator, auth, persistence, upstreams
3. both post first findings through MCP
4. each polls for new messages after every meaningful discovery
5. referee or parent agent collapses contradictions and asks the next best question
6. once root cause is evidenced, one agent posts a proposed fix and validation plan
7. parent resolves the case

## Example use case

A checkout form returns 502.
- frontend agent discovers the request body includes `billingAddress.country: "United States"`
- backend agent discovers validator expects ISO-2 country codes like `US`
- fix:
  - frontend normalizes country to ISO-2
  - backend returns `400` with clear validation errors instead of an unhandled exception

## Notes on Cursor features this starter is designed around

This repo is intentionally aligned with newer Cursor capabilities:
- parallel agents / isolated worktrees
- delegated subagent work
- MCP as a first-class tool surface
- reusable task packaging via rules, skills, and plugins

I have not assumed a private internal plugin/package format beyond what Cursor publicly describes. This starter therefore ships as a normal repo with:
- a local MCP server
- reusable prompts
- a rule file
- shell scripts

You can later wrap this into a Cursor plugin if you want.

## Troubleshooting

### The agents are chatting too much and not converging
Tighten the prompts so every message must include evidence and one concrete ask.

### The agents keep guessing
Force all hypotheses to include a proposed confirmation step.

### The agents are stepping on each other's edits
Use Cursor Multi-Agents or separate worktrees/branches.

### The MCP server is not visible in Cursor
Use the snippet from `scripts/print_mcp_config.py` and adapt it to your local Cursor MCP config. Keep the Python interpreter path absolute if needed.

## Next upgrades

- SQLite persistence instead of JSON files
- WebSocket event streaming
- automatic contract diff tool
- test-result ingestion
- GitHub PR comment export
- package this as a Cursor plugin once you want one-click install
