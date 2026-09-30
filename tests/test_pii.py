from app.pii import scrub_text
from app.logging_config import scrub_event


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_vietnamese_national_id() -> None:
    national_id = "001099012345"

    out = scrub_text(f"CCCD: {national_id}")

    assert national_id not in out
    assert "REDACTED_CCCD" in out


def test_scrub_payment_card_number_formats() -> None:
    card_numbers = (
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        "4111111111111111",
    )

    for card_number in card_numbers:
        out = scrub_text(f"Card: {card_number}")
        assert card_number not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_structured_log_fields_recursively() -> None:
    event = {
        "session_id": "contact 0901234567",
        "payload": {"notes": ["send to student@vinuni.edu.vn"]},
    }

    scrubbed = scrub_event(None, "info", event)

    assert "0901234567" not in scrubbed["session_id"]
    assert "REDACTED_PHONE_VN" in scrubbed["session_id"]
    assert "student@vinuni.edu.vn" not in scrubbed["payload"]["notes"][0]
    assert "REDACTED_EMAIL" in scrubbed["payload"]["notes"][0]
