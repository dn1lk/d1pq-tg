from typing import Dict, Any, Callable, Awaitable, Optional

from aiogram import Bot, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18n

from bot.locales.middleware import I18nContextMiddleware
from bot.utils.database.context import DataBaseContext
from bot.utils.database.middleware import DataBaseContextMiddleware


class UnoFSMContextMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        state: Optional[FSMContext] = data.get('state')

        if state:
            chat_id = await state.storage.get_data(state.bot, self.get_key(state))

            if chat_id:
                bot: Bot = data['bot']
                chat = await bot.get_chat(chat_id.get('0'))

                state.key = StorageKey(
                    bot_id=state.key.bot_id,
                    chat_id=chat.id,
                    user_id=chat.id,
                    destiny=state.key.destiny,
                )

                data.update(
                    {
                        'event_chat': chat,
                        'state': state,
                        'raw_state': await state.get_state(),
                    }
                )

                db: DataBaseContext = data['db']
                db.key = self.get_key(state, 'database')

                data['db'] = db

                i18n_middleware: I18nContextMiddleware = data['i18n_middleware']
                return await i18n_middleware(handler, event, data)

        return await handler(event, data)

    @staticmethod
    def get_key(
            state: FSMContext,
            destiny: str = 'uno_room',
    ):
        return StorageKey(
            bot_id=state.key.bot_id,
            chat_id=state.key.chat_id,
            user_id=state.key.user_id,
            destiny=destiny,
        )
