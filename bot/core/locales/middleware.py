from typing import TYPE_CHECKING, Any

from aiogram import types
from aiogram.utils.i18n import SimpleI18nMiddleware

if TYPE_CHECKING:
    from utils import database


class I18nContextMiddleware(SimpleI18nMiddleware):
    async def get_locale(self, event: types.TelegramObject, data: dict[str, Any]) -> str:
        main_settings: database.MainSettings = data["main_settings"]

        return main_settings.locale or await super().get_locale(event=event, data=data)
