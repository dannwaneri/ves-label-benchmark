"""One entry point for every item kind, and the infrastructure-failure rule.

Infrastructure failure (status "infra"): the reply is empty, hit max_tokens,
or stopped early -- for JSON items, no JSON object at all; for uncued
reports, no Recommendation field after the last Curve type field. These are
excluded from model scores and reported per model (Daniel, post-pilot).
The same rule decides the single in-task retry.
"""

from scoring.score import extract_last_json, score_item  # removed when inlined into a Kaggle task
from scoring.uncued import is_incomplete, score_uncued  # removed when inlined into a Kaggle task


def is_uncued(item):
    return "stations" in item


def incomplete(item, reply):
    if is_uncued(item):
        return is_incomplete(reply)
    if not reply or not reply.strip():
        return True
    return extract_last_json(reply)[0] is None


def score_any(item, reply, truncated=False):
    if is_uncued(item):
        return score_uncued(item, reply, truncated)
    if truncated or incomplete(item, reply):
        return {"id": item["id"], "status": "infra", "pass": False, "truncated": bool(truncated)}
    return score_item(item, reply, truncated)
