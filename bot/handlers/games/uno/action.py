import asyncio
from random import choice

from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .cards import UnoCard
from .data import UnoData
from .exceptions import UnoNoCardsException
from .. import keyboards as k


class UnoAction:
    def __init__(self, message: types.Message, state: FSMContext, data: UnoData):
        self.message: types.Message = message
        self.state: FSMContext = state

        self.data: UnoData | None = data

        from .bot import UnoBot

        self.bot: UnoBot = UnoBot(message, state.bot, data)

    async def prepare(self, card: UnoCard, accept: str):
        self.data.current_user = self.data.next_user = self.message.from_user

        try:
            await self.data.current_card_update(card)

            if len(self.data.users[self.data.current_user.id]) == 1:
                await self.uno()

        except UnoNoCardsException:
            if self.data.current_user.id == self.state.bot.id:
                await self.message.answer(
                    _("Well, I have run out of cards. I have to remain only an observer =(.")
                )
            else:
                await self.message.answer(
                    _("{user} puts his last card and leaves the game as the winner.").format(
                        user=get_username(self.data.current_user))
                )

            self.data.next_user = await self.data.user_prev(self.state.bot, self.message.chat.id)
            await self.data.user_remove(self.state)

        await self.process(accept)

    async def uno(self):
        self.data.uno_users_id.append(self.data.current_user.id)
        name = ':'.join((str(self.bot), str(self.data.current_user.id), 'uno'))

        if self.data.current_user.id == self.state.bot.id:
            await self.message.answer(
                _("I have one card left!"),
                reply_markup=k.uno_uno(),
            )

            asyncio.create_task(self.bot.uno(), name=name)
        else:
            await self.message.answer(
                _("Player {user} has one card left!").format(user=get_username(self.data.current_user)),
                reply_markup=k.uno_uno(),
            )

            asyncio.create_task(self.bot.uno_user(self.data.current_user), name=name)

    async def process(self, accept: str):
        await self.draw_check()
        self.data.current_special.color = self.data.current_special.skip = False
        await self.color_check(await self.data.card_special(self.state.bot, self.message.chat) or accept)

    async def draw_check(self):
        if self.data.current_special.draw and (not self.data.current_card.special.draw or not self.message.sticker):
            await self.message.answer(
                await self.data.user_card_add(
                    self.state.bot,
                    self.data.current_special.skip,
                    self.data.current_special.draw,
                )
            )

            self.data.current_special.draw = 0

    async def color_check(self, answer: str):
        if self.data.current_special.color:
            if self.data.current_user.id == self.state.bot.id:
                answer = await self.bot.get_color()
            else:
                return await self.message.reply(answer, reply_markup=k.uno_color())

        await self.move(answer)

    async def move(self, answer: str | None = ""):
        self.data.next_user = await self.data.user_next(self.state.bot, self.message.chat.id)
        cards = await self.bot.get_cards()

        if cards or self.state.bot.id == self.data.next_user.id:
            asyncio.create_task(self.bot.gen(self.state, cards), name=str(self.bot))
        else:
            self.message = await self.message.reply(
                answer + "\n\n" + choice(
                    (
                        _("{user}, your turn."),
                        _("{user}, your move."),
                        _("Now {user} is moving."),
                        _("Player's turn {user}."),
                        _("I pass the turn to the player {user}."),
                    )
                ).format(user=get_username(self.data.next_user)),
                reply_markup=k.uno_show_cards(),
            )

        from . import uno_timeout
        from .. import timer

        await self.state.update_data(uno=self.data)
        timer(self.state, uno_timeout, message=self.message, data_uno=self.data)

    async def end(self):
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and task.get_name().startswith('uno'):
                task.cancel()

        for poll in self.data.polls_kick.values():
            await self.state.bot.delete_message(self.message.chat.id, poll.message_id)

        self.data.current_user = (
            await self.state.bot.get_chat_member(
                self.message.chat.id,
                tuple(self.data.users)[0],
            )
        ).user

        await self.data.user_remove(self.state)
        await self.state.clear()

        await self.message.answer(
            _(
                "<b>Game over.</b>\n\n{user} is the last player."
            ).format(
                user=get_username(self.data.current_user)
            ),
            reply_markup=types.ReplyKeyboardRemove()
        )
