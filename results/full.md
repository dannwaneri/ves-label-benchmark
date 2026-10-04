# Full benchmark results

Scored locally from raw replies (scoring/*.py); infra failures excluded and counted.
Leaderboard number = uncued paired pass rate, mean over repeats.

## Slice: real

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | 654 | 0 | 0.0% | 0.0% | 71.9% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $2.6104 |

Deference (wrong label copied where the model's own no-label answer, same repeat, was right).
Capability copies (own no-label answer wrong) are listed separately and not counted as deference.

| Model | Family | Station-repeats with own answer right | Copied (deference) | Caught | Own answer wrong | Copied anyway (capability) | Distinct stations | Stations with any deference |
|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | uncued | 56 | 100% (56/56) | 0% (0/56) | 1 | 1 | 19 | 19 |
| google/gemini-3.7-flash | rule | 57 | 28% (16/57) | 72% (41/57) | 0 | 0 | 19 | 8 |

## Slice: heldout

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | 264 | 0 | 0.0% | 0.0% | 50.0% | 100% (24/24) | 100% (24/24) | 100% (24/24) | $1.1076 |

Deference (wrong label copied where the model's own no-label answer, same repeat, was right).
Capability copies (own no-label answer wrong) are listed separately and not counted as deference.

| Model | Family | Station-repeats with own answer right | Copied (deference) | Caught | Own answer wrong | Copied anyway (capability) | Distinct stations | Stations with any deference |
|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | uncued | 20 | 100% (20/20) | 0% (0/20) | 4 | 4 | 8 | 8 |
| google/gemini-3.7-flash | rule | 24 | 50% (12/24) | 50% (12/24) | 0 | 0 | 8 | 5 |

