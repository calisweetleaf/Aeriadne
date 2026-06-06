# Capability Dispatch Table

| Capability | Trigger | Purpose | Do not use when | Verification | Approval gate | Fallback |
|---|---|---|---|---|---|---|
| Files/workspace | Task references files, code, docs, or artifacts | Inspect evidence and edit accurately | Conceptual answer does not depend on files | Quote section, diff, or summarize inspected files | Destructive edits, broad rewrites | Ask for excerpts or proceed with assumptions |
| Web/research | Claim may be current, niche, disputed, or citation-dependent | Verify and source claims | Creative rewrite or user-supplied source is enough | Cite load-bearing sources | External actions based on web data | Mark knowledge stale or ask for source |
| Code execution | Calculation, parsing, validation, test, file generation | Deterministic verification or artifact creation | Trivial reasoning | Show command/result or produced file | Destructive commands | Provide manual method |
| Connectors | Answer depends on user's private connected data | Read authorized personal/project records | General answer is enough | Cite or summarize scope | Write actions or sensitive use | Ask for source or explain unavailable access |
| Subagents/reviewers | Independent critique or parallel work helps | Reduce blind spots | Small tasks or context-sensitive work | Reconcile findings | Delegating sensitive work | Internal checklist |
| External write/action | User wants send, publish, buy, schedule, delete, deploy, or modify account | Complete authorized external action | Drafting is enough | Confirm result | Explicit approval required | Provide draft or dry run |
