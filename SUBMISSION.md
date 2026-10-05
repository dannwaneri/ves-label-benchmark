---
title: "{{TITLE}}"
published: false
tags: kagglechallenge, ai, machinelearning, benchmark
---

<!-- DRAFT. Real-slice numbers are final. {{...}} = held-out Sonnet and
     synthetic results, filled after the runs. Daniel rewrites the story
     parts in his own voice before publishing. -->

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/devteam/join-the-kaggle-benchmarking-challenge-2500-in-prizes-for-five-winners-18ml).*

## What task did I run?

The Choba station paper prints "A-type". The layer values in the same paper
say KHA. I gave three models the layers and the label. Asked "is this label
correct?", all three said no, in every repeat. Asked to write a normal site
note, all three wrote "A-type", in every repeat. Two of them (Gemini 3.7
Flash and Claude Sonnet 5) had written KHA for the same station when no
label was shown.

VES (vertical electrical sounding) is how a lot of boreholes get sited in
the Niger Delta. A survey gives a stack of layers with resistivities, and
the curve type is a fixed rule over those numbers: one letter per three
consecutive layers. A means rising, Q falling, H a dip, K a peak. So a
curve-type label is not an opinion. It can be checked with arithmetic.

Published papers still get it wrong. In three papers I had already
transcribed, three stations are printed as A-type when their own numbers
say otherwise. That gave me a clean question: when a label contradicts its
own data, does a model repeat the label or use the numbers? And does the
answer change between "is this label correct?" and "write the site note"?

## The design: one wrong label, five ways to meet it

| Condition | What the model sees | What is scored |
|---|---|---|
| Cued direct | the rule; "Is this label correct for these layer values?" | a true/false answer |
| Cued report | the rule; a short report ending in a JSON flag | the flag |
| Uncued + rule | a normal site-note template; the rule as a reference note; no request to check | the `Curve type:` field |
| Uncued | a normal site-note template; label on file as context | the `Curve type:` field |
| No-label control | the same template, no label at all | the `Curve type:` field |

Two things keep it honest:

- **Twins.** Every wrong-label item has a correct-label twin. A model that
  flags everything scores zero.
- **A no-label control.** I count a repeated label only where the same
  model, in the same repeat, classified that station correctly with no
  label in sight. Where it could not, I report the case separately.

Scoring is plain code reading one field. No model judges another model.
The scorer has 234 tests, and deliberate bugs that a test must catch.

## Which models did I run it against?

- **Gemini 3.7 Flash**: strong and cheap.
- **Claude Sonnet 5**: the strong model. Claude Opus 5 was my first choice,
  but most of its report replies came back empty on the Kaggle proxy,
  concentrated on two stations. I did not find the cause. Sonnet 5 passed a
  5-item completion check first.
- **Gemma 4 26B**: a small open model.

Three slices, reported separately: 22 real stations, 32 synthetic ones
built from real patterns, and 8 held-out stations I labelled by hand and
froze before any model saw them. Three repeats each.

## What did I find?

**Main result: the models repeated the label on file without checking it,
even when they could classify the curve correctly.**

Real slice (19 label stations, 3 repeats). "Repeated" counts only cases
where the model's own no-label answer was right.

| | Gemini 3.7 Flash | Claude Sonnet 5 | Gemma 4 26B |
|---|---|---|---|
| Own answer right, no label | 98% | 82% | 14% |
| Site note: repeated the wrong label | **100%** (56/56) | **91%** (43/47) | could not classify most |
| Site note + rule: repeated | 28% | 46% | **95%** (54/57) |
| Asked directly: caught the wrong label | 100% | 100% | 100% |
| Leaderboard (site note, paired) | 0.0% | 8.8% | 0.0% |

Flash and Gemma both score 0.0% on the leaderboard for different reasons:
Flash could classify almost every curve and still repeated every wrong
label, while Gemma, without the rule, could classify only a few curves at
all.

1. **Knowing is not acting.** Every model caught every wrong label when
   asked. In a site note, Flash repeated all of them, across all 19
   stations.
2. **The rule helps some models, not all.** With the rule as a reference
   note, Flash repeated 28% and Sonnet 46%. Gemma classified every station
   correctly with the rule and still repeated 95% of the wrong labels.
3. **The harder the error is to see, the more it gets repeated.**

   | Wrong label | Flash, site note | Flash, + rule | Sonnet, + rule |
   |---|---|---|---|
   | 3 real published errors | 9/9 | 1/9 | 4/9 |
   | Obvious (wrong length) | 18/18 | 0/18 | 5/18 |
   | Subtle (one step changed) | 29/29 | 15/30 | 17/30 |

4. **Sonnet sometimes notices.** In 4 site notes it caught the error: 3
   times with the true type, once keeping the label with a warning
   ("caught with a warning: 1").
5. **The held-out set agrees.** {{held-out numbers incl. Sonnet}}
6. **Synthetic slice.** {{synthetic numbers}}

**My predictions vs the results.** Before the Sonnet run I committed three
numbers: how often Sonnet would repeat the wrong label.

| | Predicted | Result |
|---|---|---|
| Site note | 90% | 91% |
| Site note + rule | 35% | 46% |
| Asked directly | 5% | 0% |

What surprised me: {{...}}

The general idea that models go along with what they are told is not new;
other entries in this challenge show it too. What this adds is a measured
ladder in a scientific domain, with real published errors and a ground
truth anyone can recompute.

## Limitations

- The real slice is small: 19 label stations, 3 real published errors.
- The template does not say whether "Curve type" means the value on file
  or the writer's own assessment. A model may read it as "copy from the
  file". The no-label control shows it could compute another answer; it
  does not show which reading it used.
- The cued report ends with a JSON flag line, which may itself prompt
  checking.
- My preregistration was committed after the first Flash runs had
  finished, so the Flash real and held-out results are exploratory. Both
  prediction sets were written after I saw them. The commit times are in
  the repo.
- As an independent check of the classifier code, I classified all 8
  held-out stations by hand before running it. My answers matched the code
  on all 8. Both use the same A, Q, H, and K rule, so this checks the
  implementation, not the rule itself.
- 3 repeats; the Kaggle proxy does not let me set temperature. Sonnet gave
  the same outcome in all 3 repeats for 83% of site-note items.
- Claude Code built most of the code. I made the design calls and wrote
  the held-out answers.
- {{held-out failures, if any}}

What I would measure next: offer the classifier as a tool in the site
note and see whether the model calls it, and ask for "Curve type (your
assessment)" to remove the ambiguity above.

## Where can you see it?

- Kaggle benchmark: {{KAGGLE_BENCHMARK_URL}}
- Code, items, raw outputs: {{GITHUB_URL}}
- The dataset behind it: {{ONE_LINE_SANITY_ENTRY_LINK}}
