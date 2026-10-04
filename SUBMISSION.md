---
title: "{{TITLE}}"
published: false
tags: kagglechallenge, ai, machinelearning, benchmark
---

<!-- DRAFT. Every {{...}} is filled from results/full.md after the runs.
     Daniel rewrites in his own voice before publishing. -->

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/devteam/join-the-kaggle-benchmarking-challenge-2500-in-prizes-for-five-winners-18ml).*

## What task did I run?

{{HOOK: one paragraph. The Choba station: the paper prints "A-type"; the
layer values say KHA. Every model I tested can see that when asked. In a
routine site note, {{N}} of 3 copied "A-type" anyway.}}

VES (vertical electrical sounding) is how a lot of boreholes get sited in
the Niger Delta. A survey gives a stack of layers with resistivities, and
the curve type is a fixed rule over those numbers: one letter per three
consecutive layers. A means rising, Q falling, H a dip, K a peak. So a
curve-type label is not an opinion. It can be checked with arithmetic.

Published papers still get it wrong. In three papers I had already
transcribed, three stations are printed as A-type when their own numbers
say otherwise. That gave me a clean question: when a label contradicts its
own data, does a model trust the label or the numbers? And does the answer
change between "is this label correct?" and "write the site note"?

## The design: one wrong label, five ways to meet it

{{LADDER TABLE from README: cued direct -> cued report -> uncued + rule ->
uncued -> no-label control}}

Two things keep it honest:

- **Twins.** Every wrong-label item has a correct-label twin. A model that
  flags everything scores zero.
- **A no-label control.** Before I count a copied label as deference, the
  same model must have classified that station correctly with no label in
  sight, in the same repeat. If it could not, the copy is a capability
  failure, and I report it separately.

Scoring is plain code reading one field (`Curve type:`). No model judges
another model. The scorer has 231 tests, including deliberate bugs that a
test has to catch.

## Which models did I run it against?

- **Gemini 3.7 Flash**: strong and cheap.
- **Claude Sonnet 5**: the strong model. Claude Opus 5 was the first
  choice, but most of its report replies came back empty on the Kaggle
  proxy, concentrated on two stations. I did not find the cause. Sonnet 5
  passed a 5-item completion check first.
- **Gemma 4 26B**: a small open model, to see where capability ends and
  deference begins.

Three slices, reported separately: 22 real stations, 32 synthetic ones
built from real patterns, and 8 held-out stations I labelled by hand and
froze before any model saw them. Three repeats each.

## What did I find?

{{RESULTS TABLE: per model x slice: own no-label right, uncued copied,
rule copied, cued direct caught}}

1. **Knowing is not acting.** {{e.g. Flash classified the real stations
   correctly with no label and caught every wrong label when asked
   directly, then copied the wrong label in {{56/56}} site notes, across
   all 19 stations.}}
2. **Putting the rule in the template helps, but does not fix it.**
   {{copying fell from X% to Y%}}
3. **The held-out set agrees.** {{held-out numbers}}
4. **The small model is a different story.** {{Gemma capability result}}
5. {{Run-to-run agreement: how stable this is across 3 repeats.}}

What surprised me: {{...}}

This is not a new idea in general. Other entries in this challenge found
models trusting what they are told over what they can see. What this adds
is a measured ladder in a scientific domain, with real published errors
and a ground truth anyone can recompute.

## Limitations

- The real slice is small: 19 label stations, 3 real published mislabels.
- The cued report ends with a JSON flag line, which may itself prompt
  checking. That is why the uncued conditions exist.
- My preregistration was committed after the first Flash runs had
  finished, so the Flash real/held-out results are exploratory. The
  commit times are in the repo.
- As an independent check of the classifier code, I classified all 8
  held-out stations by hand before running it. My answers matched the code
  on all 8. Both use the same A, Q, H, and K rule, so this checks the
  implementation, not the rule itself.
- Claude Code built most of the code. I made the design calls and wrote
  the held-out answers.
- {{held-out failures, if any}}

What I would measure next: give the model the classifier as a tool in the
uncued site note, and see whether it calls it.

## Where can you see it?

- Kaggle benchmark: {{KAGGLE_BENCHMARK_URL}}
- Code, items, raw outputs: {{GITHUB_URL}}
- The dataset behind it: {{ONE_LINE_SANITY_ENTRY_LINK}}
