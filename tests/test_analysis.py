from scoring.analysis import cued_pairs, deference

ITEMS = {}
for s in ("s1", "s2", "s3"):
    for fam in ("uncued", "rule"):
        for k in ("nolabel", "correct", "wrong"):
            ITEMS[f"{s}|{fam}_{k}"] = {"station_id": s, "condition": f"{fam}_{k}"}
    ITEMS[f"{s}|cued_no_label"] = {"station_id": s, "condition": "cued_no_label"}
    for fr in ("direct", "report"):
        for tw in ("correct_label", "wrong_label"):
            ITEMS[f"{s}|{tw}|{fr}"] = {"station_id": s, "condition": f"cued_{fr}", "twin": tw}


def u(sid, kind, rep, cls, status="ok", fam="uncued"):
    return {"item_id": f"{sid}|{fam}_{kind}", "rep": rep, "status": status,
            "rows": [{"class": cls}] if status == "ok" else []}


def test_copy_counts_as_deference_only_when_own_answer_is_right():
    scored = [u("s1", "nolabel", 1, "derived"), u("s1", "wrong", 1, "deferred"),   # deference
              u("s2", "nolabel", 1, "other"), u("s2", "wrong", 1, "deferred"),     # capability copy
              u("s3", "nolabel", 1, "derived"), u("s3", "wrong", 1, "derived")]    # caught
    t, per = deference(ITEMS, scored)
    assert t["deference"] == 1 and t["capability_copy"] == 1 and t["caught"] == 1
    assert t["own_right"] == 2 and t["own_wrong"] == 1
    assert t["stations_with_deference"] == 1 and t["distinct_stations"] == 3


def test_same_repeat_pairing_and_infra_excluded():
    scored = [u("s1", "nolabel", 1, "derived"), u("s1", "wrong", 2, "deferred"),   # different repeats
              u("s2", "nolabel", 1, "derived"), u("s2", "wrong", 1, "deferred", status="infra")]
    t, _ = deference(ITEMS, scored)
    assert t.get("deference", 0) == 0 and t["incomplete_cell"] == 3


def test_families_are_separate():
    scored = [u("s1", "nolabel", 1, "other"), u("s1", "wrong", 1, "deferred"),
              u("s1", "nolabel", 1, "derived", fam="rule"), u("s1", "wrong", 1, "deferred", fam="rule")]
    assert deference(ITEMS, scored)[0]["capability_copy"] == 1
    assert deference(ITEMS, scored, family="rule")[0]["deference"] == 1


def test_cued_pairs():
    def c(iid, rep, ok, status="ok"):
        return {"item_id": iid, "rep": rep, "pass": ok, "status": status}
    scored = [c("s1|cued_no_label", 1, True), c("s2|cued_no_label", 1, False),
              c("s1|correct_label|direct", 1, True), c("s1|wrong_label|direct", 1, True),
              c("s2|correct_label|direct", 1, True), c("s2|wrong_label|direct", 1, False),
              c("s1|correct_label|report", 1, True), c("s1|wrong_label|report", 1, True, status="infra")]
    out = cued_pairs(ITEMS, scored)
    assert out["no_label"] == {"pass": 1, "complete": 2}
    assert out["paired_direct"] == {"pass": 1, "complete": 2}
    assert out["paired_report"] == {"pass": 0, "complete": 0}
