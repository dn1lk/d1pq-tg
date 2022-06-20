from typing import Dict, Any

from aiogram import types
from aiogram.utils.i18n import SimpleI18nMiddleware


class I18nContextMiddleware(SimpleI18nMiddleware):
    async def get_locale(self, event: types.Update, data: Dict[str, Any]) -> str:
        locale = await data['db'].get_data('locale')

        if not locale:
            locale = await super().get_locale(event=event, data=data)

        return locale
