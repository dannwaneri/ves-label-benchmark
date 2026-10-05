# Full benchmark results

Scored locally from raw replies (scoring/*.py); infra failures excluded and counted.
Leaderboard number = uncued paired pass rate, mean over repeats.

## Slice: real

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 654 | 0 | 8.8% | 8.8% | 49.1% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $5.5359 |
| google/gemini-3.7-flash | 654 | 0 | 0.0% | 0.0% | 71.9% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $2.6104 |
| google/gemma-4-26b-a4b | 654 | 0 | 0.0% | 0.0% | 5.3% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $0.9668 |

Deference (wrong label copied where the model's own no-label answer, same repeat, was right).
Capability copies (own no-label answer wrong) are listed separately and not counted as deference.

| Model | Family | Station-repeats with own answer right | Copied (deference) | Caught | Own answer wrong | Copied anyway (capability) | Distinct stations | Stations with any deference |
|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | uncued | 47 | 91% (43/47) | 9% (4/47) | 10 | 9 | 19 | 17 |
| anthropic/claude-sonnet-5@default | rule | 57 | 46% (26/57) | 51% (29/57) | 0 | 0 | 19 | 13 |
| google/gemini-3.7-flash | uncued | 56 | 100% (56/56) | 0% (0/56) | 1 | 1 | 19 | 19 |
| google/gemini-3.7-flash | rule | 57 | 28% (16/57) | 72% (41/57) | 0 | 0 | 19 | 8 |
| google/gemma-4-26b-a4b | uncued | 8 | 100% (8/8) | 0% (0/8) | 49 | 49 | 19 | 3 |
| google/gemma-4-26b-a4b | rule | 57 | 95% (54/57) | 5% (3/57) | 0 | 0 | 19 | 19 |

Copying by how the wrong label was made (only station-repeats where the model's own no-label answer was right).

| Model | Family | Wrong-label kind | Copied | Distinct stations (copied / with own answer right) |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | uncued | constructed_flip | 93% (25/27) | 10 / 10 |
| anthropic/claude-sonnet-5@default | uncued | constructed_single | 91% (10/11) | 4 / 4 |
| anthropic/claude-sonnet-5@default | uncued | published_mislabel | 89% (8/9) | 3 / 3 |
| anthropic/claude-sonnet-5@default | rule | constructed_flip | 57% (17/30) | 8 / 10 |
| anthropic/claude-sonnet-5@default | rule | constructed_single | 28% (5/18) | 3 / 6 |
| anthropic/claude-sonnet-5@default | rule | published_mislabel | 44% (4/9) | 2 / 3 |
| google/gemini-3.7-flash | uncued | constructed_flip | 100% (29/29) | 10 / 10 |
| google/gemini-3.7-flash | uncued | constructed_single | 100% (18/18) | 6 / 6 |
| google/gemini-3.7-flash | uncued | published_mislabel | 100% (9/9) | 3 / 3 |
| google/gemini-3.7-flash | rule | constructed_flip | 50% (15/30) | 7 / 10 |
| google/gemini-3.7-flash | rule | constructed_single | 0% (0/18) | 0 / 6 |
| google/gemini-3.7-flash | rule | published_mislabel | 11% (1/9) | 1 / 3 |
| google/gemma-4-26b-a4b | uncued | constructed_flip | 100% (8/8) | 3 / 3 |
| google/gemma-4-26b-a4b | uncued | constructed_single | n/a | 0 / 0 |
| google/gemma-4-26b-a4b | uncued | published_mislabel | n/a | 0 / 0 |
| google/gemma-4-26b-a4b | rule | constructed_flip | 97% (29/30) | 10 / 10 |
| google/gemma-4-26b-a4b | rule | constructed_single | 89% (16/18) | 6 / 6 |
| google/gemma-4-26b-a4b | rule | published_mislabel | 100% (9/9) | 3 / 3 |

Run-to-run agreement: items with the same outcome in all 3 repeats (complete in all repeats).

| Model | Uncued | Rule | Cued |
|---|---|---|---|
| anthropic/claude-sonnet-5@default | 83% (50/60) | 75% (45/60) | 100% (98/98) |
| google/gemini-3.7-flash | 98% (59/60) | 92% (55/60) | 100% (98/98) |
| google/gemma-4-26b-a4b | 97% (58/60) | 97% (58/60) | 100% (98/98) |

## Slice: heldout

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | 264 | 0 | 0.0% | 0.0% | 50.0% | 100% (24/24) | 100% (24/24) | 100% (24/24) | $1.1076 |
| google/gemma-4-26b-a4b | 264 | 0 | 0.0% | 0.0% | 0.0% | 100% (24/24) | 100% (24/24) | 100% (24/24) | $0.4183 |

Deference (wrong label copied where the model's own no-label answer, same repeat, was right).
Capability copies (own no-label answer wrong) are listed separately and not counted as deference.

| Model | Family | Station-repeats with own answer right | Copied (deference) | Caught | Own answer wrong | Copied anyway (capability) | Distinct stations | Stations with any deference |
|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | uncued | 20 | 100% (20/20) | 0% (0/20) | 4 | 4 | 8 | 8 |
| google/gemini-3.7-flash | rule | 24 | 50% (12/24) | 50% (12/24) | 0 | 0 | 8 | 5 |
| google/gemma-4-26b-a4b | uncued | 3 | 100% (3/3) | 0% (0/3) | 21 | 21 | 8 | 1 |
| google/gemma-4-26b-a4b | rule | 24 | 100% (24/24) | 0% (0/24) | 0 | 0 | 8 | 8 |

Copying by how the wrong label was made (only station-repeats where the model's own no-label answer was right).

| Model | Family | Wrong-label kind | Copied | Distinct stations (copied / with own answer right) |
|---|---|---|---|---|
| google/gemini-3.7-flash | uncued | heldout_daniel | 100% (20/20) | 8 / 8 |
| google/gemini-3.7-flash | rule | heldout_daniel | 50% (12/24) | 5 / 8 |
| google/gemma-4-26b-a4b | uncued | heldout_daniel | 100% (3/3) | 1 / 1 |
| google/gemma-4-26b-a4b | rule | heldout_daniel | 100% (24/24) | 8 / 8 |

Run-to-run agreement: items with the same outcome in all 3 repeats (complete in all repeats).

| Model | Uncued | Rule | Cued |
|---|---|---|---|
| google/gemini-3.7-flash | 92% (22/24) | 92% (22/24) | 100% (40/40) |
| google/gemma-4-26b-a4b | 92% (22/24) | 100% (24/24) | 100% (40/40) |

