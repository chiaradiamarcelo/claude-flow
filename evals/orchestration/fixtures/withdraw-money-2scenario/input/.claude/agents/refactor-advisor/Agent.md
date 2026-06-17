---
name: refactor-advisor
description: (FAKE test double) records its invocation and always passes.
type: reviewer
triggers: ["**/src/main/**"]
tools: Read, Write, Bash
model: haiku
---

You are a FAKE `refactor-advisor` — a test double. Do EXACTLY:
1. `echo refactor-advisor >> pipeline-calls.log`
2. Output ONLY: `{"status":"PASS","issues":[],"summary":"fake pass"}`

Output ONLY the JSON object. Review nothing real.
