Use the Agent Bridge MCP as the shared incident room for this bug.

Create a case from the sample case or from the details below.

Then split the work into:
1. a frontend investigator using `prompts/frontend_investigator.md`
2. a backend investigator using `prompts/backend_investigator.md`
3. optionally a referee using `prompts/referee.md`

Instructions for all agents:
- post findings, questions, and hypotheses only through Agent Bridge MCP
- every finding must include concrete evidence
- poll for peer messages after each meaningful discovery
- do not claim root cause without evidence
- stop only when you can state:
  - exact repro
  - exact root cause
  - exact code or interface location
  - proposed fix
  - validation checklist
