from typing import Optional

from aiogram import Bot, types
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k

from .manager import UnoManager
from .cards import UnoCard
from ... import get_username


class UnoNoUsersException(BaseException):
    pass


class UnoAction:
    def __init__(self, message: types.Message, bot: Bot, data: UnoManager):
        self.message: types.Message = message
        self.bot: Bot = bot

        self.data = data

    async def update(self, card: UnoCard, action: str):
        no_card = self.data.update_card(self.bot, card)
        if no_card:
            await self.message.answer(no_card)

            if len(self.data.users) == 1:
                raise UnoNoUsersException("Only one user remained in UNO game")

        await self.special(action)

    async def special(self, action: str):
        special = await self.data.card_special(self.bot, self.message.chat)

        if not self.data.now_card.special.draw and self.data.now_special.draw:
            await self.message.answer(
                await self.data.add_card(
                    self.bot,
                    self.data.now_special.draw.user,
                    self.data.now_special.draw.amount
                )
            )

            self.data.now_special.draw = None

        await self.next(special or action)

    async def next(self, answer: str):
        if self.data.now_card.special.color:
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

        if self.data.now_user.id != self.bot.id:
            await self.message.reply(
                answer + _("\n\n{user}, твоя очередь.").format(user=get_username(self.data.now_user)),
                reply_markup=k.game_uno_show_cards()
            )
        else:
            from .bot import gen

            self.data = await gen(self)

    async def remove(self, state, data):
        await self.data.next_user(self.bot, self.message.chat)
        await self.message.answer(
            _(
                "<b>Игра закончена.</b>\n\n{user} остался последним игроком."
            ).format(user=get_username(self.data.now_user)))

        await state.set_state()
        await state.set_data(data)
