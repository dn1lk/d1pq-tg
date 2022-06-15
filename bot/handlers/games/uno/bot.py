import asyncio
from random import choice

from aiogram import types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from .exceptions import UnoNoUsersException
from .manager import UnoManager


class UnoBot:
    def __init__(self, message: types.Message, bot: Bot, data: UnoManager):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data: UnoManager = data

    def __str__(self):
        return f'game:{self.message.chat.id}:uno:bot'

    async def uno(self):
        async with ChatActionSender.typing(chat_id=self.message.chat.id, interval=1):
            await asyncio.sleep(choice(range(3, 8)))

            self.data.uno_users_id.remove(self.bot.id)
            await self.message.answer(str(k.UNO), reply_markup=types.ReplyKeyboardRemove())

    async def get_color(self) -> str:
        color = self.data.current_card.color = choice(self.data.users[self.bot.id]).color
        return _("Я выбираю {color} цвет.").format(color=color.value[0] + " " + str(color.value[1]))

    def get_cards(self, user: types.User):
        for card in self.data.users[user.id]:
            card, accept, decline = self.data.card_filter(user, card)

            if accept:
                yield card, accept

    async def gen(self, state: FSMContext, cards: tuple | None):
        from .action import UnoAction

        action = UnoAction(message=self.message, state=state, data=self.data)

        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id, interval=1):
            await asyncio.sleep(choice(range(3, 5)))

            if cards:
                action.data.current_card, accept = choice(cards)
                action.message = self.message = await self.message.answer_sticker(action.data.current_card.file_id)

                try:
                    await action.prepare(action.data.current_card, accept)
                except UnoNoUsersException:
                    await action.end()
            else:
                await action.move(await action.data.user_card_add(self.bot))

        await state.update_data(uno=action.data)
