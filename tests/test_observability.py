from consultai.services.observability import increment, metrics_snapshot


def test_metrics_snapshot_is_non_sensitive_and_incrementable() -> None:
    before = metrics_snapshot()["requests_total"]
    increment("requests_total")
    after = metrics_snapshot()["requests_total"]
    assert after == before + 1
    assert all("email" not in key and "text" not in key for key in metrics_snapshot())
