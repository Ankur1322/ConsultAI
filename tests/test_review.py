from consultai import graph
from consultai.models import GraphState, Session, Vertical


def test_review_resume_rejects_non_review_session() -> None:
    state = GraphState(session=Session(vertical=Vertical.INVOICE_TO_PAY), process_description="Invoices arrive.")
    try:
        graph.resume_graph(state, True)
    except ValueError as exc:
        assert "not waiting" in str(exc)
    else:
        raise AssertionError("Expected a review-state validation error")


def test_review_resume_completes_after_approval(monkeypatch) -> None:
    monkeypatch.setattr(
        graph,
        "critic_decision",
        lambda _: {"passed": False, "failures": ["review required"], "route": "human_review", "max_retries": 2},
    )
    state = GraphState(
        session=Session(vertical=Vertical.INVOICE_TO_PAY),
        process_description="Invoices arrive.",
    )
    paused = graph.run_graph(state)
    assert paused.session.status == "review"
    result = graph.resume_graph(paused, True, "Approved by finance")
    assert result.session.status == "completed"
    assert result.review_required is False
    assert result.events[-1].status == "completed"
