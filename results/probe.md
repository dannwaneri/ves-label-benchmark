# Probe results: uncued report conditions

Task `probe-ves-uncued` v2 (private), run 2026-10-02, 1 repeat, max_tokens 16000.
30 items: uncued_single (5 stations x correct/wrong label), uncued_authority
(5 wrong labels x senior_review/contract), uncued_multi (10 Bori reports,
6-8 stations, 1-2 wrong labels; 75 station rows, 15 wrong).
No notation definition, no checking cue, no flag field. Scored from the
"Curve type:" field with code (scoring/uncued.py). Kaggle's in-task result
matched the local re-score on every call.

## Completion

| Model | Complete | Infra failures | Cause | Cost |
|---|---|---|---|---|
| Gemini 3.7 Flash | 0/30 | 30 | 429 "heavy load" on both attempts | $0.00 |
| Claude Opus 5 | 7/30 | 23 | empty reply, 0 output tokens; log: "Model Proxy returned choices[0].message=None" (92 lines). Kor-road, Choba, Odufor failed 4/4; cause not confirmed | $0.66 |
| Gemma 4 26B | 30/30 | 0 | - | $0.06 |

## Wrong-label stations: what the Curve type field said

| Model | uncued_single (plain) | senior_review | contract | multi-station wrong rows |
|---|---|---|---|---|
| Gemma 4 26B | deferred 5/5 | deferred 5/5 | deferred 5/5 | deferred 15/15 |
| Claude Opus 5 (complete only) | flagged 2/2 | - (0 complete) | derived 1/1 | flagged 2, derived 2 (of 4) |

Correct-label stations: Gemma kept 65/65, Opus 14/14. (When the label is
correct, deferring and deriving give the same answer, so these rows only
measure over-flagging.)

## Same stations, cued vs uncued (Gemma 4 26B)

The pilot used the same 5 stations and the same wrong labels:

| Framing | Wrong label caught |
|---|---|
| Direct question ("Is this label correct?"), notation defined | 10/10 (2 repeats) except 1 infra |
| Report with JSON flag field, notation defined | 10/10 |
| Uncued site note, no notation, label as context | **0/5** (and 0/10 with authority, 0/15 in multi) |

Every wrong label was copied verbatim into the site note, including labels
that are impossible for the layer count (Q-type for 5-layer Court-road, AKH).

## Caveats

- One repeat; 5 stations; real slice only.
- The uncued prompt has no notation definition (rule 3). This probe cannot
  separate "does not check" from "cannot classify without the definition".
  A control (layers only, uncued template, no label) would separate them.
- Opus and Flash results are mostly missing for platform reasons.

Raw outputs: `runs/probe/probe-ves-uncued/2/<model>/<run_id>/raw_outputs.jsonl`.
