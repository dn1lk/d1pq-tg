import asyncio
from random import choice

from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .cards import UnoCard
from .data import UnoData
from .exceptions import UnoNoCardsException, UnoOneCardException
from .. import keyboards as k


class UnoAction:
    def __init__(self, message: types.Message, state: FSMContext, data: UnoData):
        self.message: types.Message = message
        self.state: FSMContext = state

        self.data: UnoData | None = data

        from .bot import UnoBot

        self.bot: UnoBot = UnoBot(message, state.bot, data)

    async def prepare(self, card: UnoCard, accept: str):
        self.data.current_user_id = self.data.next_user_id = self.message.from_user.id

        try:
            self.data.update_current_card(card)

        except UnoOneCardException:
            await self.uno()

        except UnoNoCardsException:
            await self.remove()

        await self.process(accept)

    async def uno(self):
        self.data.uno_users_id.append(self.data.current_user_id)

        if self.data.current_user_id == self.state.bot.id:
            coro = self.bot.uno
            answer = _("I have one card left!")
        else:
            coro = self.bot.uno_user
            answer = _("Player {user} has one card left!").format(user=get_username(self.message.from_user))

        await self.message.answer(answer, reply_markup=k.uno_uno())

        name = str(self.bot) + ':' + str(self.data.current_user_id) + ':' + 'uno'
        asyncio.create_task(coro(), name=name)

    async def remove(self):
        if self.message.from_user.id == self.state.bot.id:
            answer = _("Well, I have run out of cards. I have to remain only an observer =(.")
        else:
            answer = _("{user} puts his last card and leaves the game as the winner.").format(
                user=get_username(self.message.from_user)
            )

        await self.message.answer(answer)

        self.data.next_user_id = self.data.user_prev()
        await self.data.remove_user(self.state)

    async def process(self, special: str = ""):
        if self.data.current_card.special.reverse:
            special = self.data.special_reverse().format(user=get_username(self.message.from_user))
        else:
            if self.data.current_card.special.color:
                color = self.data.special_color().format(user=get_username(self.message.from_user))
                return await self.user_color(special, color)

            if self.data.current_card.special.skip:
                special = self.data.special_skip().format(
                    user=get_username(await self.data.get_user(self.state.bot, self.message.chat.id))
                )

            if self.data.current_card.special.draw:
                special = self.data.special_draw().format(
                    user=get_username(await self.data.get_user(self.state.bot, self.message.chat.id))
                )
            elif self.data.current_special.draw:
                await self.user_draw()
            else:
                self.data.current_special.skip = 0

        await self.move(special)

    async def user_color(self, accept: str, color: str):
        if self.message.from_user.id == self.state.bot.id:
            await self.message.reply(self.bot.get_color())
            await self.process(accept)
        else:
            await self.state.update_data(uno=self.data.dict())
            await self.message.reply(color, reply_markup=k.uno_color())

    async def user_draw(self):
        await self.message.answer(
            await self.data.add_card(
                self.state.bot,
                self.message.chat.id,
                self.data.current_special.skip,
                self.data.current_special.draw,
            )
        )

        self.data.current_special.draw = self.data.current_special.skip = 0

    async def skip(self):
        answer = await self.data.add_card(self.state.bot, self.message.chat.id, self.data.next_user_id)

        if self.data.current_special.draw:
            await self.user_draw()

        self.data.current_user_id = self.data.current_special.skip = self.message.from_user.id
        await self.move(answer)

    async def move(self, answer: str = ""):
        self.data.next_user_id = self.data.user_next()
        cards = self.bot.get_cards()

        if cards or self.state.bot.id == self.data.next_user_id:
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
                ).format(user=get_username(await self.data.get_user(self.state.bot, self.message.chat.id))),
                reply_markup=k.uno_show_cards(),
            )

        from . import uno_timeout
        from .. import timer

        await self.state.update_data(uno=self.data.dict())
        timer(self.state, uno_timeout, message=self.message, data_uno=self.data)

    async def end(self):
        answer = await self.data.end(self.state)
        await self.message.answer(
            answer.format(user=get_username(await self.data.get_user(self.state.bot, self.message.chat.id))),
            reply_markup=types.ReplyKeyboardRemove(),
        )
