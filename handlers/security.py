import logging

from config.settings import Settings
from handlers.callbacks import answer_callback


logger = logging.getLogger(__name__)


async def require_admin_callback(callback, settings: Settings) -> bool:
    if callback.from_user.id == settings.admin_id:
        return True

    logger.warning(
        "Отклонен админский callback пользователя %s: %s",
        callback.from_user.id,
        callback.data,
    )
    await answer_callback(callback)
    return False
