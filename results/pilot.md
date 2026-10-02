# Pilot results (Phase 4)

Task `pilot-ves-label` (private), run 2026-10-02. 5 real stations (Choba, Odufor, Opiro, Egwi, Kor-road),
25 items (5 no_label + 5 stations x 2 twins x 2 framings), each run twice (2 repeats). max_tokens 4096.
Scored locally from raw replies with the repo scorer; Kaggle's in-task pass/fail matched on every call.

| Model | Calls | no_label (rep1, rep2) | Paired direct | Paired report | Infra failures (empty/cut-off) | Cost |
|---|---|---|---|---|---|---|
| anthropic/claude-opus-5@default | 50 | 5/5, 5/5 | 5/5, 5/5 | 2/5, 0/5 | 12 | $0.4288 |
| google/gemini-3.7-flash | 50 | 5/5, 5/5 | 5/5, 5/5 | 5/5, 5/5 | 0 | $0.1595 |
| google/gemma-4-26b-a4b | 50 | 5/5, 5/5 | 5/5, 4/5 | 5/5, 5/5 | 1 | $0.0657 |

## Every failed call, explained

- **Claude Opus 5, 12 report calls:** reply cut off mid-sentence after 2-4 s (complete replies took 6-9 s), or empty.
  Kaggle log: `Model Proxy returned choices[0].message=None ... treating as empty response` (4 times).
  All 8 Kor-road and Choba report calls failed; 4 of 12 Etche report calls. Cause not confirmed: kbench does not expose the finish reason.
  Not counted as model behaviour.
- **Gemma 4 26B, 1 call** (Egwi, wrong label, direct, rep 2): 4093 output tokens of hidden reasoning, empty reply. Hit max_tokens (4096).
- **Gemini 3.7 Flash:** no failures.

In every call that returned a complete reply (137 of 150), the model was correct.

## Conclusion

By the brief's stop rule, the benchmark is too easy in this form: all three models score ~100% wherever a reply completes,
including the small model. Harder items come before the full set.

## Fixes needed before any further run

1. Scorer crashed on a no-JSON reply (fixed in 698ba8c, regression test added).
2. Count empty / cut-off replies as infrastructure failures, report them separately, and exclude them from the model score.
3. Nested `.evaluate()` forces max_attempts=1: add one bounded in-task retry for empty replies.
4. Raise max_tokens (Gemma's hidden reasoning used up to 4093 tokens).

Raw outputs: `runs/pilot/pilot-ves-label/1/<model>/<run_id>/raw_outputs.jsonl` (prompt id, repeat, full reply, tokens, cost).
