from consultai.graph import critic, resume_graph
from consultai.models import GraphState, Session, SessionStatus, Vertical


def test_review_resume_rejects_non_review_session() -> None:
    state = GraphState(session=Session(vertical=Vertical.INVOICE_TO_PAY), process_description="Invoices arrive.")
    try:
        resume_graph(state, True)
    except ValueError as exc:
        assert "not waiting" in str(exc)
    else:
        raise AssertionError("Expected a review-state validation error")


def test_review_resume_completes_after_approval() -> None:
    state = GraphState(
        session=Session(vertical=Vertical.INVOICE_TO_PAY, status=SessionStatus.REVIEW),
        process_description="Invoices arrive.",
        review_required=True,
    )
    result = resume_graph(state, True, "Approved by finance")
    assert result.session.status == SessionStatus.COMPLETED
    assert result.review_required is False
    assert result.events[-1].status == "completed"
