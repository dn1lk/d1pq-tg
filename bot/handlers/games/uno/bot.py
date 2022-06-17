import asyncio
from random import choice

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from .data import UnoData
from .exceptions import UnoNoUsersException


class UnoBot:
    def __init__(self, message: types.Message, bot: Bot, data: UnoData):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data: UnoData = data

    def __str__(self):
        return f'game:{self.message.chat.id}:uno:bot'

    async def get_color(self) -> str:
        self.data.current_card.color = choice(self.data.users[self.bot.id]).color
        return _("I choice {color[0]} {color[1]} color.").format(color=self.data.current_card.color.value)

    async def get_cards(self) -> tuple:
        def get():
            for card in self.data.users.get(user.id, []):
                card, accept, decline = self.data.card_filter(user, card)
                if accept:
                    yield card, accept

        user = await self.bot.get_me()
        return tuple(get())

    async def gen(self, state: FSMContext, cards: tuple | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(1, 5)))

            from .action import UnoAction

            action_uno = UnoAction(self.message, state, self.data)

            if cards:
                action_uno.data.current_card, accept = choice(cards)
                action_uno.message = await action_uno.message.answer_sticker(action_uno.data.current_card.file_id)

                try:
                    await action_uno.prepare(action_uno.data.current_card, accept)
                except ValueError:
                    return await action_uno.message.delete()
                except UnoNoUsersException:
                    await action_uno.end()
            else:
                await action_uno.draw_check()
                await action_uno.move(await action_uno.data.user_card_add(self.bot))
                action_uno.data.current_user = self.message.from_user.id

        await state.update_data(uno=action_uno.data)

    async def uno(self):
        async with ChatActionSender.typing(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(0, 5)))

            self.data.uno_users_id.remove(self.bot.id)
            await self.message.answer(str(k.UNO), reply_markup=types.ReplyKeyboardRemove())
