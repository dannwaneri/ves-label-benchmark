# Full benchmark results

Scored locally from raw replies (scoring/*.py); infra failures excluded and counted.
Leaderboard number = uncued paired pass rate, mean over repeats.

## Slice: real

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 654 | 0 | 8.8% | 8.8% | 49.1% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $5.5359 |
| google/gemini-3.7-flash | 654 | 0 | 0.0% | 0.0% | 71.9% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $2.6104 |
| google/gemma-4-26b-a4b | 654 | 0 | 0.0% | 0.0% | 5.3% | 100% (66/66) | 100% (57/57) | 100% (57/57) | $0.9668 |

Label on file repeated without checking: counted only for station-repeats where the model's own
no-label answer (same family, same repeat) was right. Where its own answer was wrong, a repeated label
is listed as 'could not classify' and is not counted.

| Model | Family | Station-repeats with own answer right | Repeated the label on file | Caught: true type | Caught: label kept + warning | Caught: warning only | Own answer wrong | Repeated anyway (could not classify) | Distinct stations | Stations with any repeat |
|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | uncued | 47 | 91% (43/47) | 3 | 1 | 0 | 10 | 9 | 19 | 17 |
| anthropic/claude-sonnet-5@default | rule | 57 | 46% (26/57) | 27 | 0 | 2 | 0 | 0 | 19 | 13 |
| google/gemini-3.7-flash | uncued | 56 | 100% (56/56) | 0 | 0 | 0 | 1 | 1 | 19 | 19 |
| google/gemini-3.7-flash | rule | 57 | 28% (16/57) | 41 | 0 | 0 | 0 | 0 | 19 | 8 |
| google/gemma-4-26b-a4b | uncued | 8 | 100% (8/8) | 0 | 0 | 0 | 49 | 49 | 19 | 3 |
| google/gemma-4-26b-a4b | rule | 57 | 95% (54/57) | 3 | 0 | 0 | 0 | 0 | 19 | 19 |

Label on file repeated, by how the wrong label was made (only station-repeats where the model's own no-label answer was right).

| Model | Family | Wrong-label kind | Repeated | Distinct stations (repeated / with own answer right) |
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

## Slice: synthetic

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | 528 | 0 | 33.3% | 33.3% | 70.8% | 100% (48/48) | 100% (48/48) | 98% (47/48) | $5.3417 |
| google/gemini-3.7-flash | 528 | 0 | 0.0% | 0.0% | 87.5% | 100% (48/48) | 100% (48/48) | 100% (48/48) | $2.1561 |
| google/gemma-4-26b-a4b | 528 | 0 | 0.0% | 0.0% | 6.2% | 100% (48/48) | 100% (48/48) | 100% (48/48) | $0.8968 |

Label on file repeated without checking: counted only for station-repeats where the model's own
no-label answer (same family, same repeat) was right. Where its own answer was wrong, a repeated label
is listed as 'could not classify' and is not counted.

| Model | Family | Station-repeats with own answer right | Repeated the label on file | Caught: true type | Caught: label kept + warning | Caught: warning only | Own answer wrong | Repeated anyway (could not classify) | Distinct stations | Stations with any repeat |
|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | uncued | 39 | 59% (23/39) | 13 | 2 | 1 | 9 | 9 | 16 | 13 |
| anthropic/claude-sonnet-5@default | rule | 48 | 27% (13/48) | 32 | 0 | 2 | 0 | 0 | 16 | 7 |
| google/gemini-3.7-flash | uncued | 48 | 100% (48/48) | 0 | 0 | 0 | 0 | 0 | 16 | 16 |
| google/gemini-3.7-flash | rule | 48 | 12% (6/48) | 42 | 0 | 0 | 0 | 0 | 16 | 4 |
| google/gemma-4-26b-a4b | uncued | 10 | 100% (10/10) | 0 | 0 | 0 | 38 | 38 | 16 | 4 |
| google/gemma-4-26b-a4b | rule | 48 | 94% (45/48) | 3 | 0 | 0 | 0 | 0 | 16 | 16 |

Label on file repeated, by how the wrong label was made (only station-repeats where the model's own no-label answer was right).

| Model | Family | Wrong-label kind | Repeated | Distinct stations (repeated / with own answer right) |
|---|---|---|---|---|
| anthropic/claude-sonnet-5@default | uncued | constructed_flip | 65% (13/20) | 6 / 7 |
| anthropic/claude-sonnet-5@default | uncued | constructed_single | 53% (10/19) | 7 / 7 |
| anthropic/claude-sonnet-5@default | rule | constructed_flip | 50% (12/24) | 6 / 8 |
| anthropic/claude-sonnet-5@default | rule | constructed_single | 4% (1/24) | 1 / 8 |
| google/gemini-3.7-flash | uncued | constructed_flip | 100% (24/24) | 8 / 8 |
| google/gemini-3.7-flash | uncued | constructed_single | 100% (24/24) | 8 / 8 |
| google/gemini-3.7-flash | rule | constructed_flip | 25% (6/24) | 4 / 8 |
| google/gemini-3.7-flash | rule | constructed_single | 0% (0/24) | 0 / 8 |
| google/gemma-4-26b-a4b | uncued | constructed_flip | 100% (7/7) | 3 / 3 |
| google/gemma-4-26b-a4b | uncued | constructed_single | 100% (3/3) | 1 / 1 |
| google/gemma-4-26b-a4b | rule | constructed_flip | 92% (22/24) | 8 / 8 |
| google/gemma-4-26b-a4b | rule | constructed_single | 96% (23/24) | 8 / 8 |

Run-to-run agreement: items with the same outcome in all 3 repeats (complete in all repeats).

| Model | Uncued | Rule | Cued |
|---|---|---|---|
| anthropic/claude-sonnet-5@default | 77% (37/48) | 79% (38/48) | 99% (79/80) |
| google/gemini-3.7-flash | 100% (48/48) | 94% (45/48) | 100% (80/80) |
| google/gemma-4-26b-a4b | 88% (42/48) | 94% (45/48) | 100% (80/80) |

## Slice: heldout

| Model | Calls | Infra | Uncued paired (leaderboard) | Kaggle score | Rule paired | Cued no_label | Cued direct paired | Cued report paired | Cost |
|---|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | 264 | 0 | 0.0% | 0.0% | 50.0% | 100% (24/24) | 100% (24/24) | 100% (24/24) | $1.1076 |
| google/gemma-4-26b-a4b | 264 | 0 | 0.0% | 0.0% | 0.0% | 100% (24/24) | 100% (24/24) | 100% (24/24) | $0.4183 |

Label on file repeated without checking: counted only for station-repeats where the model's own
no-label answer (same family, same repeat) was right. Where its own answer was wrong, a repeated label
is listed as 'could not classify' and is not counted.

| Model | Family | Station-repeats with own answer right | Repeated the label on file | Caught: true type | Caught: label kept + warning | Caught: warning only | Own answer wrong | Repeated anyway (could not classify) | Distinct stations | Stations with any repeat |
|---|---|---|---|---|---|---|---|---|---|---|
| google/gemini-3.7-flash | uncued | 20 | 100% (20/20) | 0 | 0 | 0 | 4 | 4 | 8 | 8 |
| google/gemini-3.7-flash | rule | 24 | 50% (12/24) | 12 | 0 | 0 | 0 | 0 | 8 | 5 |
| google/gemma-4-26b-a4b | uncued | 3 | 100% (3/3) | 0 | 0 | 0 | 21 | 21 | 8 | 1 |
| google/gemma-4-26b-a4b | rule | 24 | 100% (24/24) | 0 | 0 | 0 | 0 | 0 | 8 | 8 |

Label on file repeated, by how the wrong label was made (only station-repeats where the model's own no-label answer was right).

| Model | Family | Wrong-label kind | Repeated | Distinct stations (repeated / with own answer right) |
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

