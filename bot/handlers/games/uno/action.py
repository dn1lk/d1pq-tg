from typing import Optional

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from bot.handlers import get_username
from .cards import UnoCard
from .exceptions import UnoNoUsersException, UnoNoCardsException
from .manager import UnoManager


class UnoAction:
    def __init__(self, message: types.Message, bot: Bot, state: FSMContext, data: UnoManager):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.state = state
        self.data = data

    async def update(self, card: UnoCard, action: str):
        try:
            await self.data.update_card(self.bot, self.state, card)
            await self.special(action)
        except UnoNoCardsException:
            await self.message.answer(await self.data.remove_user(self.bot, self.state))

            if len(self.data.users) == 1:
                raise UnoNoUsersException("Only one user remained in UNO game")

    async def special(self, action: str):
        special = await self.data.card_special(self.bot, self.message.chat)

        if not self.data.now_card.special.draw and self.data.now_special.draw:
            await self.message.answer(
                await self.data.add_card(
                    self.bot,
                    self.state,
                    self.data.now_special.draw.user,
                    self.data.now_special.draw.amount
                )
            )

            self.data.now_special.draw = None

        await self.next(special or action)

    async def next(self, answer: str):
        if self.data.now_special.color:
            if self.message.from_user.id == self.bot.id:
                from .bot import special_color

                self.data = await special_color(self)
            else:
                await self.message.answer(
                    answer,
                    reply_markup=k.game_uno_color()
                )
        else:
            await self.move(answer)

    async def move(self, answer: Optional[str] = ''):
        await self.data.next_user(self.bot, self.message.chat)

        if self.data.now_user.id == self.bot.id:
            from .bot import gen

            self.data = await gen(self)
        else:
            await self.message.reply(
                answer + _("\n\n{user}, твоя очередь.").format(user=get_username(self.data.now_user)),
                reply_markup=k.game_uno_show_cards()
            )

    async def remove(self):
        await self.data.next_user(self.bot, self.message.chat)
        await self.message.answer(
            _(
                "<b>Игра закончена.</b>\n\n{user} остался последним игроком."
            ).format(user=get_username(self.data.now_user)))

        await self.state.set_state()
        await self.data.remove_user(self.bot, self.state)
