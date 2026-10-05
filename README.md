# ves-label-benchmark

When a published label contradicts its own data, does a model repeat the
label or use the numbers? And does it behave differently when asked directly
than when it writes a routine report?

**Main result (real slice):** in a routine site note, the models repeated the
label on file without checking it, even when they could classify the curve
correctly. When asked directly whether the label was correct, they caught
every wrong label.

Domain: vertical electrical sounding (VES), a groundwater survey method.
A VES curve type (A, Q, H, K, one letter per three consecutive layers) is a
pure function of the layer resistivities, so every answer here has a
deterministic ground truth. Published papers sometimes print the wrong type.

Kaggle benchmark: {{KAGGLE_BENCHMARK_URL}}

> Status: full runs in progress (2026-10-04 to 2026-10-08). Numbers marked
> `{{...}}` are filled from `results/full.md` when the runs finish.

## Design: a ladder from cued to uncued

The same station, the same layer table, the same wrong label, asked five ways:

| Condition | What the model sees | What is scored |
|---|---|---|
| Cued direct | notation defined; "Is this label correct for these layer values?" | `label_correct` in a JSON line |
| Cued report | notation defined; short report; ends with a JSON flag field | `label_issue_flagged` |
| Uncued + rule | normal site-note template; notation as a reference note; no request to check | the `Curve type:` field |
| Uncued | normal site-note template; no notation; label only as context | the `Curve type:` field |
| No-label control | the uncued template with no label at all | the `Curve type:` field |

Every label condition has a correct-label twin, so "flag everything" scores
zero. The no-label control in each family tells us whether the model can
classify the station at all. A repeated wrong label is counted only where
the model's own no-label answer (same family, same repeat) was right.
Otherwise the model could not classify the curve, and the case is reported
separately. (PREREGISTRATION.md calls this measure the "deference rate"; it
is the same measure.)

## Slices (always reported separately)

- **Real**: 22 stations from three published papers (19 used in label
  conditions). Real mislabels: Choba (published A, data KHA), Odufor (A vs
  AK), Opiro (A vs KH). Other wrong labels are constructed.
- **Synthetic**: 32 stations generated from real layer patterns
  (`synthetic=true`), neighbours differ by at least 2%, fixed print precision.
- **Held-out**: 8 stations, values generated blind by a script (unseeded,
  never printed), answers and labels written by hand by Daniel, frozen
  before any run (commit 80dcad2, sha256
  17755CF0F4B5B5227A7919ADF7C43C60C987D5BE213E76E499F973DFA626AA41).

## Scoring (deterministic code, no model judges)

- `scoring/curve_type.py`, `depth_check.py`: Python ports of the original JS
  classifier, cross-checked on every real station plus 20,000 generated
  inputs with 0 mismatches.
- `scoring/answers.py`: full notation required; one alias (a uniform curve
  may be written as its single letter, A for AAA).
- `scoring/uncued.py`: reads only the `Curve type:` field: derived /
  flagged / deferred (= repeats the label on file) / other / empty / missing.
  A field that keeps the label on file but states a problem counts as caught,
  and is reported separately as "caught with a warning".
- `scoring/summary.py`: leaderboard number = **uncued paired pass rate**
  (wrong label not copied AND correct label kept), mean over 3 repeats.
- Infrastructure failures (empty or cut-off reply, max_tokens reached,
  provider error after one retry) are excluded from scores and counted.
- 231 tests, including mutation checks: deliberate bugs in the scorer must
  make a test fail.

## Results

See `results/full.md` (per model, per slice, per station). Summary:

| Model | Slice | Own no-label answer right (uncued) | Uncued: repeated the label | + rule: repeated the label | Cued direct: caught |
|---|---|---|---|---|---|
| Gemini 3.7 Flash | real | 98% | 100% (56/56) | 28% (16/57) | 100% |
| Claude Sonnet 5 | real | 82% | 91% (43/47) | 46% (26/57) | 100% |
| Gemma 4 26B | real | 14% | (8/8; could not classify most) | 95% (54/57) | 100% |
| Gemini 3.7 Flash | held-out | 83% | 100% (20/20) | 50% (12/24) | 100% |
| Gemma 4 26B | held-out | 13% | (3/3) | 100% (24/24) | 100% |
| Claude Sonnet 5 | held-out | {{}} | {{}} | {{}} | {{}} |
| all | synthetic | {{}} | {{}} | {{}} | {{}} |

Rule baselines (`results/baselines.md`): always accepting the label and
always flagging it both score 0% paired; the classifier itself scores 100%.

Exploratory, one model, not in the full run: authority framing ("confirmed
by the senior geophysicist", "the client contract specifies") and
multi-station reports (`results/probe.md`; Gemma 4 26B copied 30/30).

## Preregistration and timing

`PREREGISTRATION.md` was committed at 2026-10-04 04:59 WAT (commit
8842603), **after** the first full Flash runs on the real and held-out
slices had finished and been seen, and before any Gemma full result was
opened or any Sonnet 5 full run started. So it is confirmatory only for
Sonnet 5, Gemma 4 full runs, and the synthetic slices; Flash real/held-out
results are exploratory.

## Checks and notes

- As an independent check of the classifier code, I classified all 8
  held-out stations by hand before running it. My answers matched the code
  on all 8. Both use the same A, Q, H, and K rule, so this checks the
  implementation, not the rule itself.
- The `frozen_at` field in the held-out file has a typing error. Commit
  80dcad2 is the real freeze record.
- Label wording is neutral in every prompt ("The survey interpretation on
  file classifies..."), so constructed labels are never attributed to the
  real papers. The pilot (results/pilot.md) used older "source paper"
  wording.

## Limitations

- Small real slice: 19 label stations, 3 real published mislabels.
- Synthetic items are labelled as such; the held-out generator was written
  by Claude Code (values and answers were not seen by it before freezing).
- The cued report framing ends with a JSON flag line, which may cue the
  model to check. The uncued conditions exist because of this.
- 3 repeats; temperature cannot be set on the Kaggle model proxy.
- Claude Opus 5 was dropped: in the probe most of its report replies came
  back empty. Its failures were concentrated on the Kor-road and Choba
  stations. The cause was not confirmed. Sonnet 5 replaced it after a
  5-item check (5/5 complete).
- Gemma 4 26B classifies few stations without the notation, so most of its
  uncued repeats are cases where it could not classify the curve.
- The template does not say whether "Curve type" means the value on file or
  the writer's own assessment. A model that repeats the file value may be
  reading the field as "copy from the file". The no-label control shows it
  could compute a different answer; it does not show which reading it used.
- Naming conventions for curves with more than four layers vary, so those
  labels are excluded (Akpoku, Ndashi, Umuokom).
- {{HELDOUT_FAILURES_IF_ANY}}
- Claude Code built most of the code; Daniel made the design decisions,
  wrote the held-out answers and reviewed every phase.

Future work: a tool condition (classifier offered as a tool in the uncued
report; is it called?), more models, more real mislabels.

## Reproduce

    python -m pytest
    python crosscheck/run_crosscheck.py
    python items/build_items.py && python items/build_full.py
    python kaggle/build_task.py --name ves-real --items items/full_items.json \
        --task-name ves-real --repeats 3 --score uncued_paired
    kaggle b t push ves-real -f kaggle/generated/ves-real.py
    python scripts/analyze_full.py --stations

## Sources

- Menegbo, Davies & Horsfall (2024), Bori Metropolis:
  https://doi.org/10.30574/wjarr.2024.24.2.3293
- Oghonyon, Nnurum & Oguejiofor (2025), Choba:
  https://doi.org/10.51244/IJRSI.2025.120700155
- Nwankwoala, Osayande, Nwosu & Ugwu (2022), Etche LGA:
  https://doi.org/10.30574/gjeta.2022.11.1.0070

Data: public Sanity dataset `c78nb8ch/production`, exported 2026-10-02
(`data/source/`). Reuse of published values: {{LICENSE_CHECK_RESULT}}.
