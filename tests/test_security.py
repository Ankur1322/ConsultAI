from consultai.services.redaction import redact_pii


def test_redaction_removes_common_pii() -> None:
    result = redact_pii("Contact alice@example.com or +1 555-123-4567.")
    assert "alice@example.com" not in result.text
    assert "555-123-4567" not in result.text
    assert result.count == 2
    assert set(result.entity_types) == {"EMAIL_ADDRESS", "PHONE_NUMBER"}


def test_redaction_does_not_count_unsupported_presidio_entities() -> None:
    result = redact_pii("Contact alice@example.com for more information.")
    assert result.count == 1
    assert result.entity_types == ("EMAIL_ADDRESS",)


def test_redaction_is_idempotent_for_safe_text() -> None:
    result = redact_pii("Invoices require manager approval.")
    assert result.text == "Invoices require manager approval."
    assert result.count == 0
