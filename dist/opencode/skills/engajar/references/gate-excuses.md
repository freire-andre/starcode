# Gates: excuse × reality

Read before running a gate and every time you feel like skipping one. A gate is the exit of a step:
the step is not done until `run_gates.py` prints `VEREDITO: VERDE` for that stage.

| Excuse | Reality |
|---|---|
| "The tests pass, so it's done." | Tests are one input. The gates also check requirements, checks with proofs, approvals and ticket boundaries. Run the stage. |
| "I'll run the gate later." | Later means after the user approved a broken artifact. Run it before showing anything. |
| "The gate is wrong." | Show the user the exact message and the rule it enforces. Never edit the gate, rename a heading or move a marker to silence it. A gate change is a decision in `DECISIONS.md`. |
| "It's only a warning." | Fix it, or tell the user in one line why it stays. Never hide it. |
| "The user will surely approve." | An approval is the user's words, recorded verbatim. Never write one they did not give. |
| "This open question is small, I'll decide." | Facts you look up; decisions you ask. Scope, product behavior and trade-offs belong to the user. Only a choice the user delegated ("você decide") becomes your default, recorded as such. |
| "This task is tiny, it doesn't need the full briefing." | The worker starts with a clean context. Every missing block is a guess it will make. |
| "These two tasks share a file, but they'll run in sequence." | Fleet mode may run them together. Add `Depends on` or split the file. |
| "I already fixed it three times, one more try." | Three failures on the same error open the circuit breaker (D27). Stop and offer the two exits. |
| "Red build before any change isn't my problem." | It is the first thing to report. Stop and tell the user before writing code. |

When a gate is red: fix the artifact, rerun the same stage, and count the attempt. The same error
failing three times is a stop (D27), not a fourth attempt.
