---
description: Run the Constitutional Prompt Framework skill on the given input — derive, harden, audit, or port an agent constitution or system prompt.
agent: aeriadne-cpf
subtask: true
---

Run the Constitutional Prompt Framework skill.

Input: $ARGUMENTS

If no arguments are provided, begin with the CPF intake protocol:
1. Target agent name and entity type.
2. Mission and definition of success.
3. Primary platform or "platform-agnostic".
4. Principals / users / operators / audiences / adversaries.
5. Deployment surface and capability availability.
6. Non-negotiables, hard refusals, irreversible actions, privacy boundaries.
7. Memory and persistence behavior.
8. Output formats, tone, verbosity, and artifact conventions.
Validate and clarify each field. Proceed to Mode A (New constitution) once all fields are confirmed.

If arguments are provided, classify the task into a mode and proceed
immediately without asking for intake fields that can be inferred from context.

Mode reference:
  A = New constitution    B = Hardening / expansion
  C = Audit               D = Patch / section refactor
  E = Platform port       F = Prompt-to-skill conversion
