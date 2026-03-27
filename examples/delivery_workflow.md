# Example: Delivery Workflow

**Scenario:** The root cause of the checkout 502 is known (from `debugging_workflow.md`). Now you want the frontend and backend agents to implement the fix, with an E2E test to validate. You want backend to go first, then frontend, then E2E — without manually sequencing them yourself.

---

## What you type — start to finish

### Step 1 — Orchestrator window

> Create a feature to fix the checkout country code mismatch identified in case `checkout-502-001`. The fix has two parts: the backend serializer needs to accept both "US" and "USA" and return a 422 (not 502) for invalid country codes; the frontend needs to normalize the country dropdown value to ISO-2 before submitting. Add these acceptance criteria:
> - Backend returns 422 with a clear error when country is not ISO-2
> - Frontend normalizes country names to ISO-2 before submission
> - E2E tests pass for US, CA, and GB addresses
> - No regressions in the existing checkout flow
>
> Create a contract for the checkout request payload specifying that `billingAddress.country` must be ISO 3166-1 alpha-2. Create tasks for backend (no dependencies), frontend (depends on backend), and E2E (depends on both). Then dispatch.

The orchestrator creates the feature, contract, task graph, and dispatches. It will confirm that the backend task is immediately available and the frontend and E2E tasks are waiting on their dependencies.

---

### Step 2 — Backend repo window

> Pick up your next task for feature `feat-checkout-country-001` and implement it. Read the contract before writing any code.

That's it. Leave it alone.

---

### Step 3 — Frontend repo window

> Pick up your next task for feature `feat-checkout-country-001` and implement it. Read the contract before writing any code.

That's it. Leave it alone.

---

## What happens next (you're not involved)

**Backend agent:**
- Claims the backend task
- Reads the contract
- Implements the serializer fix and adds specs
- Posts file references and test results as artifacts
- Marks the task complete

**The system (automatically):**
- Detects the backend task is complete
- Unlocks the frontend task
- Frontend agent's next `get_next_task` call returns it immediately

**Frontend agent:**
- Was waiting — now claims the frontend task
- Reads the same contract
- Implements the country normalization
- Posts artifacts and marks complete

**The system (automatically):**
- Detects both tasks are complete
- Unlocks the E2E task

**E2E agent** (if you have one running):
- Claims the E2E task
- Reads what was built (artifacts from both agents)
- Runs tests and posts results
- Marks complete

**The system (automatically):**
- All tasks complete → feature status flips to `resolved`

---

## Checking in (optional)

At any point:

> What's the current status of feature `feat-checkout-country-001`? Which tasks are done and what's next?

The agent will call `process_events` and give you a plain-English summary with next-action hints.

---

## If something blocks

An agent will mark its task as blocked with a specific reason — for example:

> "Blocked: the contract doesn't specify the error payload shape for 422 responses."

You'll see this if you check in. To unblock:

> Update the contract for feature `feat-checkout-country-001` to specify that a 422 response includes `{errors: [{field, message}]}`. Then tell the backend agent to resume its task.

The orchestrator updates the contract; the backend agent re-reads it and continues.

---

## How the task sequencing works

You never told the frontend agent to wait for the backend. The dependency was encoded in the task graph when the orchestrator created it. The system enforces it:

```
backend task (no deps) → available immediately
frontend task (depends on backend) → available after backend completes
E2E task (depends on both) → available after both complete
```

When you prompted the frontend agent in Step 3, it called `get_next_task` — and got nothing, because the backend wasn't done yet. It waited and polled. The moment the backend marked its task complete, the frontend task unlocked and the frontend agent claimed it on the next poll. No human involvement.
