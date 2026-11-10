from consultai.graph import NODE_NAMES, run_stub_graph
from consultai.models import GraphState, Session, Vertical


def test_stub_graph_runs_all_typed_nodes() -> None:
    state = GraphState(
        session=Session(vertical=Vertical.CUSTOMER_SUPPORT),
        process_description="Support agents answer password-reset questions.",
    )
    result = run_stub_graph(state)
    assert [event.node for event in result.events] == list(NODE_NAMES)
    assert result.session.status == "completed"
    assert result.requirements is not None
    assert result.process_map is not None
    assert result.research is not None
