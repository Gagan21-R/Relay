"""Phase 11: evaluation results are produced and exposed, per language, with the synthetic-data disclaimer."""


def test_metrics_endpoint_has_all_metrics(client):
    m = client.get("/api/metrics").json()
    assert m["available"] and "synthetic" in m["disclaimer"]
    for s in ("development", "held_out"):
        assert m[s]["duplicates"]["overall"]["precision"] is not None and m[s]["duplicates"]["per_language"]
        assert set(m[s]["extraction"]["overall"]) == {"zone", "need", "people"}
        assert set(m[s]["fake_true_confusion"]) == {"tp", "fp", "tn", "fn"}
    assert {"te", "mr", "bn"} <= set(m["held_out"]["languages"])
    o = m["operations"]
    for k in ("plan_generation_seconds", "evidence_traceability", "shortage_detection", "delivery_verification"):
        assert k in o
