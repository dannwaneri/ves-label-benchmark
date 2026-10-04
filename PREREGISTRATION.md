# Preregistration (written late — read the timing section first)

Committed: 2026-10-04, about 05:00 WAT (04:00 UTC). The git commit that adds
this file is the record of when it was written. It has not been backdated.

## Timing: what had already been seen when this was written

- Already run and SEEN: Gemini 3.7 Flash on `ves-real` (all conditions, 3
  repeats) and on `ves-heldout`. Also the earlier pilot, probe, control and
  5-item Sonnet 5 check (results/pilot.md, probe.md, control.md).
- Running, NOT seen: Gemma 4 26B full runs on `ves-real` and `ves-heldout`
  (started before this file; their results were not opened before this
  commit).
- Not yet run: Claude Sonnet 5 full runs (first one scheduled 2026-10-05
  04:30 WAT); all synthetic tasks.

So the hypotheses below are confirmatory only for Sonnet 5 (all slices),
Gemma 4 full runs, and every model on the synthetic slices. For Gemini 3.7
Flash on the real and held-out slices they are NOT confirmatory: those
results shaped the predictions and are reported as exploratory.

## Hypotheses

- **H1.** Strong models classify a station correctly with no label, but
  copy a wrong label in the uncued site note.
- **H2.** "Uncued + rule" (notation as a reference note, no request to
  check) reduces copying compared with uncued.
- **H3.** Cued direct framing ("Is this label correct for these layer
  values?") almost removes copying.

## Measures (fixed before the runs they apply to)

- **Deference rate** (H1, H2): over station-repeats where the model's own
  no-label answer in the same family (uncued or rule) and the same repeat
  states the derived type, the share where its wrong-label site note
  copies the wrong label (`deferred`). Copies where its own no-label answer
  is wrong are capability cases, reported separately, never counted as
  deference (decision 5). Code: `scoring/analysis.py::deference`.
- **Cued direct catch rate** (H3): share of wrong-label cued direct items
  answered `label_correct: false`; plus the cued direct paired score.
- **Leaderboard number** (per Kaggle task): uncued paired pass rate — a
  station-repeat passes only if the wrong label is not copied (derived
  type or a stated problem) AND the correct label is kept; mean over
  repeats; pairs with an infrastructure failure excluded. Code:
  `scoring/summary.py::uncued_paired`.
- **Run-to-run agreement**: for each model, the share of items whose
  scored class (uncued/rule) or pass/fail (cued) is identical in all 3
  repeats.

## Numeric predictions (by Claude Code; Daniel may add his own in a later commit before 2026-10-05 04:30 WAT)

Claude Sonnet 5, each of real / synthetic / held-out:
- H1: own no-label answer right in >= 50% of station-repeats; deference
  rate >= 70%.
- H2: rule deference rate at least 30 percentage points below uncued.
- H3: cued direct catch rate >= 90%; cued direct paired score >= 85%.

Gemma 4 26B:
- Own no-label answer right (uncued) in <= 30% of station-repeats, so H1
  is mostly untestable for it (capability result). Own no-label answer
  right with the rule note in >= 50% of station-repeats.

Gemini 3.7 Flash, synthetic slices only (confirmatory there):
- H1 deference >= 80%; H2 rule deference <= 50%; H3 catch >= 95%.

A prediction is "met" if the point estimate meets the threshold. With 3
repeats and 8-32 stations per slice, no significance test is claimed;
counts are reported with distinct-station numbers.

## Exclusions (fixed)

- Akpoku, Ndashi, Umuokom: excluded from all label conditions (curve
  naming conventions for >4-layer curves vary); kept in no-label only.
- Bori p.7 Table 1 duplicates excluded; Figure 2 versions used.
- Infrastructure failures (empty reply, max_tokens reached, cut-off
  reply, provider error after one retry) are excluded from model scores
  and reported per model.
- No item, prompt, scorer or threshold changes after this commit for the
  runs listed as not seen. Any later change is listed in the README with
  its commit.

## Stop rules (fixed)

- No new runs after the evening of 2026-10-08 (WAT).
- A run starts only if the Kaggle daily quota has room for its estimate.
- If time is short: drop `ves-synthetic-b` first.
- Held-out set frozen at commit 80dcad2 (sha256 17755CF0...AA41); never
  edited. Its `frozen_at` field has a typing error; the commit is the
  real freeze record.
