import asyncio
from random import choice

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .data import UnoData
from .exceptions import UnoNoUsersException
from .. import keyboards as k


class UnoBot:
    def __init__(self, message: types.Message, bot: Bot, data: UnoData):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data: UnoData = data

    def __str__(self):
        return 'uno' + ':' + str(self.message.chat.id) + ':' + 'bot'

    def get_color(self):
        self.data.current_card.color = choice(self.data.users[self.bot.id]).color
        return _("I choice {emoji} {color} color.").format(
            emoji=self.data.current_card.color.value,
            color=self.data.current_card.color.get_color(),
        )

    def get_cards(self) -> tuple:
        def get():
            for card in self.data.users[self.bot.id]:
                card, accept, decline = self.data.card_filter(self.bot.id, card)
                if accept:
                    yield card, accept

        if self.bot.id in self.data.users:
            return tuple(get())

    async def gen(self, state: FSMContext, cards: tuple | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(0, 3)))

            from .action import UnoAction

            action_uno = UnoAction(self.message, state, self.data)

            if cards:
                action_uno.data.current_card, accept = choice(cards)
                action_uno.message = await action_uno.message.answer_sticker(action_uno.data.current_card.file_id)

                try:
                    await action_uno.prepare(
                        action_uno.data.current_card,
                        accept.format(user=get_username(action_uno.message.from_user))
                    )
                except ValueError:
                    return await action_uno.message.delete()
                except UnoNoUsersException:
                    await action_uno.end()
            else:
                await action_uno.skip()

    async def uno(self):
        async with ChatActionSender.typing(chat_id=self.message.chat.id):
            await asyncio.sleep(choice(range(0, 2)))

            self.data.uno_users_id.remove(self.bot.id)
            await self.message.answer(str(k.UNO), reply_markup=types.ReplyKeyboardRemove())

    async def uno_user(self):
        await asyncio.sleep(choice(range(2, 6)))

        await self.data.add_card(self.bot, self.message.chat.id, self.message.from_user.id, 2)
        await self.message.answer(
            get_username(self.message.from_user) + ", " + str(k.UNO),
            reply_markup=types.ReplyKeyboardRemove())
