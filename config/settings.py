import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


TOKEN_PLACEHOLDER = "PASTE_YOUR_BOT_TOKEN_HERE"
ADMIN_ID_PLACEHOLDER = "PASTE_YOUR_TELEGRAM_ID_HERE"
ENV_HELP = (
    "Заполните файл .env: укажите BOT_TOKEN от @BotFather "
    "и числовой ADMIN_ID вашего Telegram аккаунта."
)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    sbp_phone: Optional[str] = None
    sbp_name: Optional[str] = None
    db_path: Path = Path("stardrop.sqlite3")


def load_settings(env_file: Optional[Path] = None) -> Settings:
    load_dotenv(dotenv_path=env_file, override=env_file is not None)

    bot_token = os.getenv("BOT_TOKEN")
    admin_id = os.getenv("ADMIN_ID")
    sbp_phone = _optional_env("SBP_PHONE")
    sbp_name = _optional_env("SBP_NAME")

    if not bot_token:
        raise RuntimeError(f"BOT_TOKEN не заполнен. {ENV_HELP}")
    if not admin_id:
        raise RuntimeError(f"ADMIN_ID не заполнен. {ENV_HELP}")
    if bot_token == TOKEN_PLACEHOLDER:
        raise RuntimeError(f"BOT_TOKEN оставлен как шаблон. {ENV_HELP}")
    if admin_id == ADMIN_ID_PLACEHOLDER:
        raise RuntimeError(f"ADMIN_ID оставлен как шаблон. {ENV_HELP}")

    try:
        parsed_admin_id = int(admin_id)
    except ValueError as exc:
        raise RuntimeError(f"ADMIN_ID должен быть числом. {ENV_HELP}") from exc

    return Settings(
        bot_token=bot_token,
        admin_id=parsed_admin_id,
        sbp_phone=sbp_phone,
        sbp_name=sbp_name,
    )


def _optional_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None

    value = value.strip()
    return value or None
