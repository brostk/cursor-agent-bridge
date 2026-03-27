# Example: Debugging Workflow

**Scenario:** A checkout form is returning a 502. The frontend team suspects a payload mismatch; the backend team suspects an upstream validation error.

---

## What you type — start to finish

### Step 1 — Orchestrator window

> Investigate why the checkout form is returning a 502. The frontend is sending `billingAddress.country: "United States"` but the backend appears to expect an ISO-2 code. Use `checkout-502-001` as the case ID.

The orchestrator creates the case, confirms the ID back to you, and **immediately starts monitoring**. You'll see status updates appear in this window as the agents work.

---

### Step 2 — Frontend repo window

> Pick up case `checkout-502-001` as the frontend investigator and start tracing how the billing country field is built, transformed, and submitted.

---

### Step 3 — Backend repo window

> Pick up case `checkout-502-001` as the backend investigator and start tracing how the country value is received, serialized, and forwarded to the upstream validator.

---

## What you watch

Only the **orchestrator window**. It will report something like:

> **Update — cycle 1:**
> Frontend found that `transformFormData()` passes the full country name through unchanged. Network tab confirms `"United States"` reaches vets-api.
>
> Backend has not posted yet. I've nudged them to check the VES serializer.
>
> Leading hypothesis: country name is reaching VES without normalization. Waiting for backend to confirm what VES expects.

> **Update — cycle 2:**
> Backend confirmed: VES expects ISO-2. The serializer does no normalization. Backend also found that the city field is dropped when `country != "USA"` — which is a second bug.
>
> I've posted a message asking frontend to confirm whether their end also needs the normalization, or whether this is purely a backend responsibility.
>
> Root cause is close. Both bugs are on the backend side.

> **Update — cycle 3:**
> Both agents agree on root cause. I'm asking the backend agent to propose a fix.

---

## What you do at the end

Nothing. The orchestrator reports when the case is resolved:

> **Case resolved.**
>
> **Root cause:** Two bugs in the backend VES serializer. (1) Country name is not normalized to ISO-2. (2) City is conditionally excluded when `country != "USA"`, but the frontend sends `"US"`.
>
> **Fix:** Normalize country to ISO-2 on intake. Remove the city exclusion condition or fix the comparison to accept both "US" and "USA".
>
> **Validation steps:**
> - Submit with a US address — no VES validation errors
> - Submit with a non-US address — city is still included in the VES payload
> - Run ivc_champva VES integration specs

---

## If you want to track the fix

Tell the orchestrator:

> Create a feature linked to case `checkout-502-001` to implement the backend fix and any needed frontend changes. Plan the tasks and dispatch.

Then prompt each agent window once to pick up their task. The orchestrator monitors delivery the same way it monitored the investigation.
