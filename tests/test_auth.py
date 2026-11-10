from uuid import uuid4

from consultai.services.auth import hash_password, issue_token, verify_password


def test_password_hash_is_not_reversible_and_verifies() -> None:
    encoded = hash_password("correct horse battery staple")
    assert encoded != "correct horse battery staple"
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_tokens_have_expiry() -> None:
    token, expires_at = issue_token(uuid4())
    assert token
    assert expires_at.tzinfo is not None
