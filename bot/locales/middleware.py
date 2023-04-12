from typing import Any

from aiogram import types
from aiogram.utils.i18n import SimpleI18nMiddleware


class I18nContextMiddleware(SimpleI18nMiddleware):
    async def get_locale(self, event: types.TelegramObject, data: dict[str, Any]) -> str:
        from bot.utils import database
        db: database.SQLContext = data['db']

        try:
            chat_id: int = data.get('event_chat', data['event_from_user']).id
            locale = await db.locale.get(chat_id)
        except KeyError:
            return self.i18n.default_locale

        if not locale:
            return await super().get_locale(event=event, data=data)
        return locale
