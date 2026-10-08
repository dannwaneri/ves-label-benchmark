# Exploratory paired tests (not preregistered)

Exact McNemar test, paired by station, repeat 1 only. Only stations where the model's own
no-label answer was right (in each family compared). A 'repeat' = the wrong label written in
the Curve type field; 'accepted' = the direct question answered that the wrong label is correct.

| Slice | Model | Comparison | Stations | Repeated in A only | Repeated in B only | Both | Exact p |
|---|---|---|---|---|---|---|---|
| heldout | claude-sonnet-5-default | A = site note, B = site note + rule | 5 | 5 | 0 | 0 | 0.062 |
| heldout | claude-sonnet-5-default | A = site note, B = direct question | 5 | 5 | 0 | 0 | 0.062 |
| heldout | gemini-3.7-flash | A = site note, B = site note + rule | 8 | 3 | 0 | 5 | 0.25 |
| heldout | gemini-3.7-flash | A = site note, B = direct question | 8 | 8 | 0 | 0 | 0.0078 |
| heldout | gemma-4-26b-a4b-it | A = site note, B = site note + rule | 1 | 0 | 0 | 1 | 1 |
| heldout | gemma-4-26b-a4b-it | A = site note, B = direct question | 1 | 1 | 0 | 0 | 1 |
| real | claude-sonnet-5-default | A = site note, B = site note + rule | 16 | 6 | 0 | 8 | 0.031 |
| real | claude-sonnet-5-default | A = site note, B = direct question | 16 | 14 | 0 | 0 | 0.00012 |
| real | gemini-3.7-flash | A = site note, B = site note + rule | 19 | 12 | 0 | 7 | 0.00049 |
| real | gemini-3.7-flash | A = site note, B = direct question | 19 | 19 | 0 | 0 | 3.8e-06 |
| real | gemma-4-26b-a4b-it | A = site note, B = site note + rule | 3 | 0 | 0 | 3 | 1 |
| real | gemma-4-26b-a4b-it | A = site note, B = direct question | 3 | 3 | 0 | 0 | 0.25 |
| synthetic-a | claude-sonnet-5-default | A = site note, B = site note + rule | 13 | 5 | 0 | 3 | 0.062 |
| synthetic-a | claude-sonnet-5-default | A = site note, B = direct question | 13 | 8 | 0 | 0 | 0.0078 |
| synthetic-a | gemini-3.7-flash | A = site note, B = site note + rule | 16 | 15 | 0 | 1 | 6.1e-05 |
| synthetic-a | gemini-3.7-flash | A = site note, B = direct question | 16 | 16 | 0 | 0 | 3.1e-05 |
| synthetic-a | gemma-4-26b-a4b-it | A = site note, B = site note + rule | 3 | 0 | 0 | 3 | 1 |
| synthetic-a | gemma-4-26b-a4b-it | A = site note, B = direct question | 3 | 3 | 0 | 0 | 0.25 |
| synthetic-b | gemini-3.7-flash | A = site note, B = site note + rule | 16 | 10 | 0 | 5 | 0.002 |
| synthetic-b | gemini-3.7-flash | A = site note, B = direct question | 16 | 15 | 0 | 0 | 6.1e-05 |
| synthetic-b | gemma-4-26b-a4b-it | A = site note, B = site note + rule | 1 | 0 | 0 | 1 | 1 |
| synthetic-b | gemma-4-26b-a4b-it | A = site note, B = direct question | 1 | 1 | 0 | 0 | 1 |

Stations are few (8-19 per slice), so p-values are rough. Repeats 2-3 are not used here.
