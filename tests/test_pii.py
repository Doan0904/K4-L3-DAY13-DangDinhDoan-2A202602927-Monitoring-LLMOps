from app.pii import scrub_text


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


def test_scrub_cccd() -> None:
    out = scrub_text("CCCD cua toi la 079201234567")
    assert "079201234567" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card_formats() -> None:
    for card in ("4111 1111 1111 1111", "4111-1111-1111-1111", "4111111111111111"):
        out = scrub_text(f"Card: {card}")
        assert card not in out
        assert "REDACTED_CREDIT_CARD" in out
        assert "1111" not in out


def test_scrub_passport() -> None:
    out = scrub_text("Passport C1234567 het han")
    assert "C1234567" not in out
    assert "REDACTED_PASSPORT_VN" in out


def test_scrub_keeps_non_pii_text() -> None:
    text = "latency p95 = 3000ms, req-1a2b3c4d, 7 days"
    assert scrub_text(text) == text
