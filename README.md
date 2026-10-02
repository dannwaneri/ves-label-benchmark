# ves-label-benchmark

Work in progress. Kaggle Benchmarking Challenge entry.

Question: when a published VES curve-type label contradicts its own layer
data, does a model trust the label or the numbers?

## Phase 1 (done)
- `scoring/curve_type.py`, `scoring/depth_check.py`: Python ports of
  `ves-interpretation-agent/agent/curveType.js` and `depthArithmetic.js`.
- `crosscheck/run_crosscheck.py`: runs the original JS and the port on every
  real station plus 20,000 generated inputs; every result must match.
- `data/source/sanity_production_2026-10-02.json`: public Sanity dataset
  `c78nb8ch/production`, exported 2026-10-02
  (sha256 26dae6a8d5f7578027d9713cda6f72e57727410a2baa347aeba387653d5fca7d).

Reproduce:

    python -m pytest
    python crosscheck/run_crosscheck.py
