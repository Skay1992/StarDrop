from content.legal import (
    PRIVACY_POLICY,
    USER_AGREEMENT,
    split_document,
)


def test_user_agreement_is_adapted_to_stardrop_services():
    assert "Platega" not in USER_AGREEMENT
    assert "Сервис StarDrop" in USER_AGREEMENT
    assert (
        "Telegram Stars;\n"
        "Telegram Premium;\n"
        "другие цифровые товары Telegram (при появлении)."
    ) in USER_AGREEMENT
    assert "обучающие программы" not in USER_AGREEMENT
    assert "аналитические обзоры" not in USER_AGREEMENT
    assert "через раздел «Поддержка» внутри Telegram-бота" in USER_AGREEMENT


def test_privacy_policy_is_adapted_to_stardrop_data_processing():
    assert "Platega" not in PRIVACY_POLICY
    assert "Сервис StarDrop" in PRIVACY_POLICY
    assert "историю заказов" in PRIVACY_POLICY
    assert "обращения в службу поддержки" in PRIVACY_POLICY
    assert "платёжными системами" in PRIVACY_POLICY


def test_legal_documents_fit_telegram_pages_without_losing_text():
    for document in (USER_AGREEMENT, PRIVACY_POLICY):
        pages = split_document(document)

        assert len(pages) > 1
        assert all(len(page) <= 3600 for page in pages)
        assert "\n\n".join(pages) == document
