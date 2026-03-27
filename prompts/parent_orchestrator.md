# Parent orchestrator instruction

Use this when you want Cursor to coordinate the investigation.

You are coordinating a multi-agent debugging session.

Create or use a shared case in the Agent Bridge MCP.

Then manage three roles:
- frontend investigator
- backend investigator
- referee

## Process

1. Create the case.
2. Assign frontend-oriented work to one agent and backend-oriented work to another.
3. Require both to communicate only through Agent Bridge MCP.
4. Require all important claims to cite evidence artifacts.
5. After each round, summarize:
   - known facts
   - open questions
   - rejected hypotheses
   - leading hypothesis
6. Do not mark the case resolved until the root cause, fix, and validation plan are explicit.

## Investigation buckets

Classify the bug into one or more of:
- route mismatch
- schema mismatch
- auth/session issue
- CORS / headers / CSRF
- environment/config drift
- async timing / race
- stale contract / generated client drift
- serialization/deserialization bug
- backend exception
- upstream dependency failure
- cache inconsistency
- optimistic UI masking real failure
