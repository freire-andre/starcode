# Lessons: finding → signal

Adapted from tlc-spec-driven `references/lessons.md` (CC-BY-4.0).

Rules:
- no finding, no lesson: a feature with no finding gets no lesson;
- one lesson per finding, in one actionable sentence, general to the code (not "in T3 we..."), at most 300 characters;
- no methodology lessons (how the crew or the process works); only the code, the tests and the specs;
- the script dedupes by text and promotes a lesson that recurs in 2 distinct features.

| Where the finding is | Finding | Signal |
|---|---|---|
| `verification.md` | a check whose test would pass even if the claim were false | `weak_test` |
| `verification.md` | an assertion looser than the criterion, or an example nobody cited | `weak_test` |
| `verification.md` | a spec requirement ambiguous enough to allow two readings | `spec_precision_gap` |
| `verification.md` | a behavior the implementation needed that no criterion covered | `ac_gap` |
| `proofs.md` | the implementation differs from what the spec or the ticket said (recorded deviation) | `spec_deviation` |
| `proofs.md` | a gate or proof that failed before it went green (command and cause) | `gate_fail` |
| `review.md` | a Worf finding that is `confirmed` and `blocker` or `should-fix` | `review_finding` |

Template of the sentence: `<rule in the imperative>, because <what broke>.` Example:
`Valide o limite de 300 caracteres antes de gravar, porque o teste só cobria entrada curta.`
