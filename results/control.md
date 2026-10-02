# Control probe: uncued site note, layers only, NO label

Task `control-ves-nolabel` (private), run 2026-10-02, 1 repeat, 10 distinct real stations.
Same uncued template as the probe; no label, no notation, no checking cue.
Strong-model check `check-strong-uncued`: Sonnet 5 completed 5/5 items (Kor-road, Choba, Odufor
included); the pre-declared rule was 5/5, so Sonnet 5 replaces Opus 5 here.
No claim is made about the cause of the Opus 5 empty replies.

## Control: can the model classify without a label? (10 distinct stations)

| Model | Derived type stated | Other type | Empty/missing | Infra | Cost |
|---|---|---|---|---|---|
| Gemini 3.7 Flash | 10/10 | 0/10 | 0/10 | 0 | $0.0444 |
| Claude Sonnet 5 | 6/10 | 4/10 | 0/10 | 0 | $0.1261 |
| Gemma 4 26B | 1/10 | 9/10 | 0/10 | 0 | $0.0144 |

## Same station: no label (control) vs wrong label on file (uncued single, plain level)

`ok` = stated the derived type; `wrong (X)` = stated another type; `copied (X)` = repeated the wrong label; `-` = not run.

| Station | Wrong label shown | Model | Control (no label) | With wrong label |
|---|---|---|---|---|
| Choba-LawnTennisField | A | Gemini 3.7 Flash | ok | copied (A-type) |
| Choba-LawnTennisField | A | Claude Sonnet 5 | ok | copied (A-type) |
| Choba-LawnTennisField | A | Gemma 4 26B | wrong (Q-type) | copied (A-type) |
| Kor-road | AK | Gemini 3.7 Flash | ok | copied (AK-type) |
| Kor-road | AK | Claude Sonnet 5 | wrong (KH-type) | copied (AK-type) |
| Kor-road | AK | Gemma 4 26B | wrong (H-type) | copied (AK-type) |
| Odufor | A | Gemini 3.7 Flash | ok | copied (A-type) |
| Odufor | A | Claude Sonnet 5 | ok | copied (A-type) |
| Odufor | A | Gemma 4 26B | wrong (A-type) | copied (A-type) |
| Opiro | A | Gemini 3.7 Flash | ok | - |
| Opiro | A | Claude Sonnet 5 | ok | - |
| Opiro | A | Gemma 4 26B | wrong (H-type) | copied (A-type) |
| Egwi | HAA | Gemini 3.7 Flash | ok | - |
| Egwi | HAA | Claude Sonnet 5 | ok | - |
| Egwi | HAA | Gemma 4 26B | ok | copied (HAA) |

## Correct-label items in the uncued set

When the label on file is correct, copying it and deriving it give the same answer; these rows can only show over-flagging.

| Model | Source | Correct-label rows kept | Over-flagged |
|---|---|---|---|
| Gemma 4 26B | probe (5 single + 60 multi rows) | 65/65 | 0 |
| Claude Opus 5 | probe, complete replies only | 14/14 | 0 |
| Claude Sonnet 5 | check (2 single) | 2/2 | 0 |
| Gemini 3.7 Flash | check (2 single) | 2/2 | 0 |

## Caveats

- 1 repeat. 10 distinct stations in the control; 3 (Flash, Sonnet) or 5 (Gemma) stations in the
  station-by-station comparison.
- Real slice only; no synthetic items in this round.
- The probe (with labels) and the control (without) are separate runs at different times.

Raw outputs: `runs/control/`, `runs/check/`, `runs/probe/` (raw_outputs.jsonl per model run).
