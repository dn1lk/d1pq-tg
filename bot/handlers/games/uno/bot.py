import asyncio
from random import choice

from aiogram import types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

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
            await asyncio.sleep(choice(range(3)))

            self.data.uno_users_id.remove(self.bot.id)
            await self.message.answer(_("УНО!"), reply_markup=types.ReplyKeyboardRemove())

    async def get_color(self) -> str:
        color = self.data.current_card.color = choice(self.data.users[self.bot.id]).color
        return _("Я выбираю {color} цвет.").format(color=color.value[0] + " " + str(color.value[1]))

    async def get_cards(self, user: types.User):
        for card in self.data.users[user.id]:
            card, accept, decline = await self.data.card_filter(self.bot, self.message.chat.id, user, card)

            if accept:
                yield card, accept

    async def gen(self, state: FSMContext):
        from .action import UnoAction

        action = UnoAction(message=self.message, state=state, data=self.data)
        user = await self.bot.get_me()

        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id, interval=1):
            await asyncio.sleep(choice(range(0, 3)))

            cards = [card async for card in self.get_cards(user)]

            if cards:
                action.data.current_card, accept = choice(cards)
                action.message = await self.message.answer_sticker(action.data.current_card.file_id)

                try:
                    await action.prepare(action.data.current_card, accept)
                except UnoNoUsersException:
                    await action.end()
            else:
                action.data.current_user = action.data.next_user
                action.data.next_user = await action.data.user_next(self.bot, self.message.chat.id)
                await action.move(await action.data.user_card_add(self.bot, user))

        await state.update_data(uno=action.data)
