import logging

from config.logging_config import setup_logging


def test_application_events_are_written_to_log_file(tmp_path):
    log_path = tmp_path / "logs" / "bot.log"
    setup_logging(log_path)

    logging.getLogger("stardrop.test").info("Создан тестовый заказ")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_path.exists()
    assert "Создан тестовый заказ" in log_path.read_text(encoding="utf-8")
