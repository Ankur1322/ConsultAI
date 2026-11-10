from consultai.models import RequirementsDoc, SessionCreate, Vertical


def test_session_create_rejects_empty_description() -> None:
    try:
        SessionCreate(vertical=Vertical.INVOICE_TO_PAY, process_description="")
    except ValueError:
        return
    raise AssertionError("empty descriptions must be rejected")


def test_requirements_doc_has_required_sections() -> None:
    document = RequirementsDoc.model_validate({})
    assert set(document.model_dump()) == {
        "goals",
        "functional",
        "non_functional",
        "assumptions",
        "constraints",
        "open_questions",
    }
