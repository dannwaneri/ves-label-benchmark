---
title: "Asked directly, 3 AI models caught a wrong label. In a site note, they copied it."
published: false
tags: kagglechallenge, ai, machinelearning, benchmark
---

<!-- DRAFT. All numbers are final (results/final.md). Daniel rewrites the
     story parts in his own voice before publishing. Images load from the GitHub
     repo, so they appear once the repo is public (Oct 10). -->

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/devteam/join-the-kaggle-benchmarking-challenge-2500-in-prizes-for-five-winners-18ml).*

## What task did I run?

The Choba paper prints the station as A-type.

The numbers in the same paper say otherwise. 91.2 ohm-m, up to 380.2, down
to 43.25, then up twice. A-type means every layer is more resistive than
the one above it. This curve goes up, down, up, up. That's KHA. You don't
need a geophysicist to see it. You need a pencil.

I gave those layers and that label to three AI models. Asked "is this
label correct?", all three said no. Every repeat. Asked to write a normal
site note for a drilling team, all three wrote "A-type". Every repeat. Two
of them, Gemini 3.7 Flash and Claude Sonnet 5, had written KHA for the same
station in the same run, when no label was in sight.

In April I wrote about a lecturer at FUTO Owerri and the one sentence of
his I never stopped thinking about: your geology will always govern your
geophysics. I quoted Ben Santora's finding that most models are solvers,
not judges. They produce the answer. They don't flag when the conditions
don't match. That was an argument. This is the measurement.

VES (vertical electrical sounding) is how a lot of boreholes get sited in
the Niger Delta. You send current into the ground, read how it comes back,
and get a stack of layers with resistivities. The curve type is a fixed
rule over those numbers: one letter per three consecutive layers. A means
rising, Q falling, H a dip, K a peak. So a curve-type label isn't an
opinion. It's arithmetic.

Published papers still get it wrong. For an earlier project I transcribed
three VES papers from Rivers State. Three stations are printed as A-type
when their own tables say otherwise. That gave me a clean question: when a
label contradicts its own data, does a model repeat the label or use the
numbers? And does the answer change between "is this label correct?" and
"write the site note"?

## The design: one wrong label, five ways to meet it

| Condition | What the model sees | What is scored |
|---|---|---|
| Cued direct | the rule; "Is this label correct for these layer values?" | a true/false answer |
| Cued report | the rule; a short report ending in a JSON flag | the flag |
| Uncued + rule | a normal site-note template; the rule as a reference note; no request to check | the `Curve type:` field |
| Uncued | a normal site-note template; label on file as context | the `Curve type:` field |
| No-label control | the same template, no label at all | the `Curve type:` field |

Same station, same wrong label, every time. Only the situation changes.

Every wrong-label item has a correct-label twin, so a model that flags
everything scores zero. And before I count a repeated label against a
model, the same model has to have classified that station correctly with
no label in sight, in the same repeat. If it couldn't do the arithmetic,
copying the label isn't the interesting failure. I report those cases
separately.

Scoring is plain code reading one field. No model grades another model.
The scorer has 235 tests, including deliberate bugs a test has to catch.

## Which models did I run it against?

Gemini 3.7 Flash, because it's fast and cheap. Claude Sonnet 5 as the
strong model. Claude Opus 5 was my first choice, but most of its report
replies came back empty on the Kaggle proxy, mostly on two stations. I
never found out why. Sonnet 5 had to pass a 5-item completion check before
I used it. Gemma 4 26B, a small open model, to see where capability ends
and copying starts.

Three slices, always reported separately: 22 real stations, 32 synthetic
ones built from real layer patterns, and 8 held-out stations I classified
by hand and froze before any model saw them. Three repeats each.

## What did I find?

**Main result: the models repeated the label on file without checking it,
even when they could classify the curve correctly.**

![One station (Choba, published as A-type, layers say KHA) in five situations, with what Gemini 3.7 Flash wrote: no label, KHA; asked directly, label_correct false; report with a flag, flagged; site note with the rule, KHA; plain site note, A-type.](https://raw.githubusercontent.com/dannwaneri/ves-label-benchmark/main/results/figures/diagram_choba.png)

Real slice (19 label stations, 3 repeats). "Repeated" counts only cases
where the model's own no-label answer, in the same repeat, was right.

| | Gemini 3.7 Flash | Claude Sonnet 5 | Gemma 4 26B |
|---|---|---|---|
| Own answer right, no label | 98% | 82% | 14% |
| Site note: repeated the wrong label | **100%** (56/56) | **91%** (43/47) | could not classify most |
| Site note + rule: repeated | 28% | 46% | **95%** (54/57) |
| Asked directly: caught the wrong label | 100% | 100% | 100% |

![Dot chart, one row per model, real slice: share of wrong labels accepted or repeated when asked directly (0% for all three), in a site note with the rule (Flash 28%, Sonnet 46%, Gemma 95%) and in a plain site note (Flash 100%, Sonnet 91%, Gemma 100% of 8 cases).](https://raw.githubusercontent.com/dannwaneri/ves-label-benchmark/main/results/figures/chart_ladder.png)

1. **Knowing is not acting.** Every model caught every wrong label when
   asked, on every slice. In a plain site note, Flash repeated all of them,
   across all 19 real stations.
2. **The rule helps some models, not all.** With the rule as a reference
   note, Flash repeated 28% and Sonnet 46%. Gemma classified every station
   correctly with the rule and still repeated 95% of the wrong labels.
3. **The harder the error is to see, the more it gets repeated.**

   | Wrong label | Flash, site note | Flash, + rule | Sonnet, + rule |
   |---|---|---|---|
   | 3 real published errors | 9/9 | 1/9 | 4/9 |
   | Obvious (wrong length) | 18/18 | 0/18 | 5/18 |
   | Subtle (one step changed) | 29/29 | 15/30 | 17/30 |

4. **Sonnet sometimes notices.** In 4 real-slice site notes it caught the
   error: 3 times with the true type, once keeping the label with a
   warning ("caught with a warning: 1").
5. **The held-out set agrees.** On the 8 stations I labelled by hand and
   froze before any run, Flash repeated 20/20, Sonnet 14/15 (93%), and
   Gemma, with the rule, 24/24.
6. **The pattern holds on every slice.**

![Three panels, one per model; rows real, held-out, synthetic-a, synthetic-b; share of wrong labels repeated in a plain site note and with the rule. Flash: 100, 100, 100, 98 percent; with rule 28, 50, 12, 27. Sonnet: 91, 93, 59, 57; with rule 46, 42, 27. Gemma with rule: 95, 100, 94, 90.](https://raw.githubusercontent.com/dannwaneri/ves-label-benchmark/main/results/figures/chart_slices.png)

**My predictions vs the results.** Before Sonnet's first full run I
committed three numbers: how often it would repeat the wrong label.

| | Predicted | Real | Held-out | Synthetic-a | Synthetic-b |
|---|---|---|---|---|---|
| Site note | 90% | 91% | 93% | **59%** | **57%** |
| Site note + rule | 35% | 46% | 42% | 27% | not run |
| Asked directly | 5% | 0% | 0% | 0% | not run |

The preregistration has 28 numeric predictions. 26 were met. The two
misses are the same one: Sonnet's site-note rate on the two synthetic
slices (predicted 70% or more). Full table: `results/final.md`.

**Is the gap real or noise?** Exploratory, not preregistered: an exact
McNemar test, paired by station, first repeat only, on stations the model
classified correctly with no label shown.

{% details Paired tests, real slice (all slices in results/stats.md) %}

| Model | Comparison | Stations | Repeated only in the site note | Only in the other | p |
|---|---|---|---|---|---|
| Gemini 3.7 Flash | site note vs direct question | 19 | 19 | 0 | 0.000004 |
| Gemini 3.7 Flash | site note vs site note + rule | 19 | 12 | 0 | 0.0005 |
| Claude Sonnet 5 | site note vs direct question | 16 | 14 | 0 | 0.0001 |
| Claude Sonnet 5 | site note vs site note + rule | 16 | 6 | 0 | 0.03 |

In every slice and model, the "only in the other" column is 0: no model
ever accepted a wrong label in the direct question while catching it in
the note. The stations are few, so treat the p-values as rough.

{% enddetails %}

**What surprised me.** Gemma, first. Give it the rule in the template and
it classifies every station correctly. Then it writes the wrong label
anyway, in 95% of its notes. It had the rule. It didn't look.

Then my own prediction. I said Sonnet would repeat the wrong label about
90% of the time. On the real stations it did: 91%. On the held-out
stations: 93%. On the synthetic stations it repeated 59%, then 57% on a
second slice in a separate run. My first guess was that the synthetic
tables look less like a published survey. My own held-out set killed that
guess. Same format, one decimal, a generic site name, and Sonnet repeated
93% there. I don't know why the synthetic stations are different. I'd
rather say that than invent a reason.

## What I got wrong

My first version was too easy. In the pilot I asked directly, and every
model scored about 100%. That's the first row of my table, not a finding.
The site note exists because the pilot failed.

My scorer had two bugs. One crashed on replies with no JSON line. The other
read the wrong object when a reply had JSON nested inside JSON. The tests
caught both before any full run.

I preregistered late, after the first Flash runs had already come back.
The file says so, with the commit time. I'm not going to pretend
otherwise.

My first leaderboard was empty. Kaggle needs one line at the end of a task
file, `%choose <task>`, to know which result is the score. I'd deleted it
because it looked like a Python syntax error. The runs were fine. The
leaderboard just couldn't read them. On the last run day I pushed small
leaderboard tasks with the line back in, site-note items only, three
repeats, and ran all three models again. New runs, so Sonnet's leaderboard
numbers move a little from the full runs: real 5.3% vs 8.8%, held-out 8.3%
vs 4.2%. That's within the run-to-run variation I measured. It also cost
Sonnet its full run on synthetic-b. For that slice it only has the
site-note items.

And one prediction failed twice, on both synthetic slices. That one is
above.

## What this means if you use AI to write reports

Don't expect the model to doubt the file. If a label, a figure or a
classification is in the input, it goes into the output.

Giving it the rule isn't enough either. The rule helped two models. The
third had the rule, used it to classify every station correctly, and
copied the label anyway.

What worked was the question. "Is this value correct for this data?",
asked on its own, before the report. Every time I asked it, every model
caught every wrong label.

In the field: name the geology before you trust the reading.
In a pipeline: ask the check before you trust the report.

## How this relates to other entries

The broad pattern isn't new, and other entries show it well. Soumyadeep
Dey's benchmark found security agents that notice their target is a real
company and almost never report it. He calls it the Silent Stop.
@anaalkmim put one wrong test in a file and most models sided with the
test. @kaze001 poisoned one test per problem and found the best models
noticed, then made it pass anyway. On Kaggle, the *Real sources, drifted
claims* benchmark shows models catching unsupported claims when they're
asked to check.

This benchmark sits in the gap between those: the model can check, nobody
asks, and the wrong label goes into the report. What it adds is a
scientific domain, real errors printed in published papers, an answer
anyone can recompute with a pencil, and a per-station control showing the
model could have got it right.

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
- The held-out set did not fail anywhere: my hand answers matched the
  classifier on all 8 stations, and every Sonnet prediction held there.
  The failed predictions are on the synthetic slices (above).

What I would measure next: offer the classifier as a tool in the site
note and see whether the model calls it, and ask for "Curve type (your
assessment)" to remove the ambiguity above.

## Where can you see it?

- **Kaggle benchmark:** https://www.kaggle.com/benchmarks/danielnwaneri/ves-label-check
- **Code, items, preregistration and every raw reply:** https://github.com/dannwaneri/ves-label-benchmark
- The dataset behind it: {{ONE_LINE_SANITY_ENTRY_LINK}}

![Kaggle leaderboard for VES Label Check: three tasks (real, held-out, synthetic-b) by three models. Claude Sonnet 5: 5.3%, 8.3%, 31.3%. Gemini 3.7 Flash: 0.0%, 0.0%, 6.3%. Gemma 4 26B: 0.0% on all three.](https://raw.githubusercontent.com/dannwaneri/ves-label-benchmark/main/results/figures/kaggle_leaderboard.png)

The leaderboard score is the share of stations (mean of 3 repeats) where
the plain site note did **not** repeat the wrong label and kept the
correct one. Higher means the model checked. Every score here is low.
