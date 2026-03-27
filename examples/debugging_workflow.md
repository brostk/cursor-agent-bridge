# Example: Debugging Workflow

**Scenario:** A checkout form is returning a 502. The frontend team suspects a payload mismatch; the backend team suspects an upstream validation error. You want both to investigate simultaneously and converge on a root cause.

---

## What you type — start to finish

### Step 1 — Orchestrator window

> Create a new agent-bridge case with ID `checkout-502-001`, title "Checkout 502 on submit", and this problem statement: "The checkout form returns a 502 intermittently on submit. The frontend sends a billing address with `country: 'United States'` but the upstream validator may expect an ISO-2 code. Neither team has confirmed where the failure originates."

The agent creates the case and confirms. That's all you do in this window for now.

---

### Step 2 — Frontend repo window

> You are the frontend investigator on case `checkout-502-001`. Use the agent-bridge MCP tools for all cross-agent communication. Start by tracing how the billing address — specifically the country field — is collected, transformed, and included in the checkout request payload. Post your first finding to the case.

Then leave it alone.

---

### Step 3 — Backend repo window

> You are the backend investigator on case `checkout-502-001`. Use the agent-bridge MCP tools for all cross-agent communication. Start by tracing what the checkout endpoint receives, how the billing address is serialized before forwarding to the upstream service, and what the upstream validator expects. Post your first finding to the case.

Then leave it alone.

---

## What happens next (you're not involved)

The agents run independently. Each one:

1. Investigates its side of the stack
2. Posts findings, hypotheses, and questions to the shared case
3. Reads what the other agent posted
4. Refines its hypothesis and posts again
5. Repeats until the root cause is clear

A typical exchange looks like this (you don't write any of this — the agents do):

- **Frontend posts:** Found that `transformFormData()` passes `country: 'United States'` through unchanged. Network tab confirms the full country name reaches the backend.
- **Backend reads it, then posts:** Confirmed — backend receives the full name. The upstream serializer maps it to a `stateCode` field and the validator rejects anything that isn't ISO-2. This is the root cause.
- **Frontend reads it, posts:** Agreed. Frontend can normalize to ISO-2 before sending. Backend should also return a 422 instead of letting it bubble to a 502.

---

## Step 4 — Resolve (any window)

When the agents have converged, ask any of them:

> Resolve case `checkout-502-001` with the root cause, proposed fix, and validation steps the agents identified.

The agent reads the findings from the case and calls `resolve_case` on your behalf.

---

## Checking in (optional)

At any point you can ask any agent:

> What's the current status of case `checkout-502-001`? Summarize what each agent has found so far.

You never need to copy messages between windows or tell either agent to "check for updates."

---

## After the investigation — tracking the fix

If you want to track the implementation as a feature:

> Create a feature linked to case `checkout-502-001` to fix the country code mismatch. The fix requires a backend serializer change and a frontend normalization step. Create tasks for each and dispatch.

Then prompt the frontend and backend windows once each to pick up their tasks. See `delivery_workflow.md` for how that plays out.
