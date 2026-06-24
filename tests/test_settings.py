from pathlib import Path

import pytest

from config.settings import load_settings


def test_load_settings_rejects_placeholder_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BOT_TOKEN=PASTE_YOUR_BOT_TOKEN_HERE\n"
        "ADMIN_ID=PASTE_YOUR_TELEGRAM_ID_HERE\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError) as error:
        load_settings(Path(env_file))

    assert "Заполните файл .env" in str(error.value)
    assert "BOT_TOKEN" in str(error.value)


def test_load_settings_accepts_filled_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BOT_TOKEN=TEST_BOT_TOKEN_FILLED_VALUE\n"
        "ADMIN_ID=123456789\n",
        encoding="utf-8",
    )

    settings = load_settings(Path(env_file))

    assert settings.bot_token == "TEST_BOT_TOKEN_FILLED_VALUE"
    assert settings.admin_id == 123456789
    assert settings.sbp_phone is None
    assert settings.sbp_name is None
    assert settings.reviews_url == "https://t.me/stardrop_reviews"


def test_load_settings_reads_payment_requisites(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BOT_TOKEN=TEST_BOT_TOKEN_FILLED_VALUE\n"
        "ADMIN_ID=123456789\n"
        "SBP_PHONE=+79990000000\n"
        "SBP_NAME=Антон\n",
        encoding="utf-8",
    )

    settings = load_settings(Path(env_file))

    assert settings.sbp_phone == "+79990000000"
    assert settings.sbp_name == "Антон"


def test_load_settings_reads_reviews_url(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BOT_TOKEN=TEST_BOT_TOKEN_FILLED_VALUE\n"
        "ADMIN_ID=123456789\n"
        "REVIEWS_URL=https://t.me/custom_reviews\n",
        encoding="utf-8",
    )

    settings = load_settings(Path(env_file))

    assert settings.reviews_url == "https://t.me/custom_reviews"
