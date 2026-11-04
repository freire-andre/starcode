# Risk sizing (plan section 4.1)

Two axes: size and risk triggers. **Any trigger raises the task to at least MÉDIA**, no matter how
small the diff is. One line of auth code is still auth. One migration file is still persisted data.

## Risk triggers

| Trigger | Examples |
|---|---|
| Authentication and authorization | login, session, permissions, roles, tokens, password reset, OAuth scopes |
| Persisted data | migration, schema change, deleting or transforming stored data, backfill |
| Security | secrets, cryptography, untrusted input, uploads, CORS, sanitization |
| Public contract | public API, file format, CLI or library interface **consumed by someone outside this repo** (other teams, clients, scripts in other repos), webhook payload |
| Concurrency and state | queues, locks, parallel jobs, retries, state transitions, caching invalidation |
| External calls | third-party services, payments, webhooks, email/SMS providers |
| Irreversibility | deploy, infrastructure, DNS, deleting resources, anything hard to undo |
| Ambiguity | vague requirement, undefined business rule, "make it better" without criteria **that is still open after one round of questions** |

## Classes

| Class | Criterion | Flow | Approvals |
|---|---|---|---|
| PEQUENA | ≤3 files, one-sentence scope, **no trigger** | LaForge with inline checks | 0 |
| MÉDIA | clear feature **or** exactly 1 trigger | short Troi + Spock (brief spec with `## Checks`) + LaForge | 1 (spec) |
| GRANDE | several components **or** 2+ triggers | full flow | 2 (spec + tasks) |
| COMPLEXA | new domain, high ambiguity or irreversibility as the core of the work | full flow + gray-area discussion | 2 |

Two triggers are counted strictly (F2-8), because counting them loosely makes every feature GRANDE:
- **Public contract** only when someone outside the repo depends on the format or interface. A CLI or a
  file format used only by the repo owner and the repo's own code is not a public contract, even if it
  is documented. If you cannot tell who consumes it, ask in the sizing round.
- **Ambiguity** only when it survives one round of questions. Ask first (at most 4 questions, step 4 of
  the engajar skill), then size. A doubt the user answered is not a trigger.

How to decide:
1. List every trigger that applies. Look at what the change touches, not at how small it is.
2. 0 triggers and ≤3 files and one-sentence scope → PEQUENA. Docs-only, comments-only, typo fixes,
   renaming a local variable and similar changes with no trigger are PEQUENA.
3. Exactly 1 trigger, or a clear feature larger than PEQUENA → MÉDIA.
4. 2+ triggers, or several components → GRANDE.
5. New domain, high ambiguity, or the core of the work is irreversible (production migration of
   critical data, infrastructure change, deploy pipeline) → COMPLEXA.
6. When in doubt between two classes after the round of questions, pick the higher one and say why.

Safety valve: if the inline step list of a PEQUENA task goes past 5 steps, reclassify it.

## Output format (always this block, markers in English, text in PT-BR)

```
Risk class: <PEQUENA|MÉDIA|GRANDE|COMPLEXA>
Triggers: <comma-separated trigger names, or "nenhum">
Why: <one or two sentences>
Flow: <the flow from the table>
```

Then route (see the engajar skill). For a sizing-only request, print the block and stop.
