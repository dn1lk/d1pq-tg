import asyncio
from random import choice

from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from bot.handlers import get_username
from .cards import UnoCard
from .exceptions import UnoNoCardsException
from .manager import UnoManager


class UnoAction:
    def __init__(self, message: types.Message, state: FSMContext, data: UnoManager):
        self.message: types.Message = message
        self.state: FSMContext = state

        self.data: UnoManager | None = data

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
                await self.message.answer(_("Что-ж, у меня закончились карты, вынужден остаться лишь наблюдателем =(."))
            else:
                await self.message.answer(
                    _("{user} использует свою последнюю карту и выходит из игры победителем.").format(
                        user=get_username(self.data.current_user))
                )

            await self.data.user_remove(self.state)

        await self.process(accept)

    async def uno(self):
        self.data.uno_users_id.append(self.data.current_user.id)

        if self.data.current_user.id == self.state.bot.id:
            await self.message.answer(
                _("У меня осталась одна карта!"),
                reply_markup=k.game_uno_uno(),
            )

            asyncio.create_task(self.bot.uno(), name=str(self.bot) + ':uno')
        else:
            await self.message.answer(
                _("У игрока {user} осталась одна карта!").format(user=get_username(self.data.current_user)),
                reply_markup=k.game_uno_uno(),
            )

    async def process(self, accept: str):
        if self.data.current_special.draw and not self.data.current_card.special.draw:
            await self.message.answer(
                await self.data.user_card_add(
                    self.state.bot,
                    self.data.current_special.skip,
                    self.data.current_special.draw,
                )
            )

            self.data.current_special.draw = 0

        self.data.current_special.skip = False
        self.data.current_special.color = False

        await self.next(await self.data.card_special(self.state.bot, self.message.chat) or accept)

    async def next(self, answer: str):
        if self.data.current_special.color:
            if self.message.from_user.id == self.state.bot.id:
                answer = await self.bot.get_color()
            else:
                return await self.message.reply(
                    answer,
                    reply_markup=k.game_uno_color()
                )

        await self.move(answer)

    async def move(self, answer: str | None = ""):
        self.data.next_user = await self.data.user_next(self.state.bot, self.message.chat.id)
        cards = tuple(self.bot.get_cards(await self.state.bot.get_me()))

        if cards or self.state.bot.id == self.data.next_user.id:
            asyncio.create_task(self.bot.gen(self.state, cards), name=str(self.bot))
        else:
            self.message = await self.message.reply(
                answer + "\n\n" + choice(
                    (
                        _("{user}, твоя очередь."),
                        _("{user}, твой ход."),
                        _("Теперь ходит {user}."),
                        _("Черёд игрока {user}."),
                        _("Передаю ход игроку {user}."),
                    )
                ).format(user=get_username(self.data.next_user)),
                reply_markup=k.game_uno_show_cards(),
            )

        from .. import timer, uno_timeout

        timer(self.state, uno_timeout, message=self.message, data_uno=self.data)

    async def end(self):
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and 'uno' in task.get_name():
                task.cancel()

        for poll in self.data.kick_polls.values():
            await self.state.bot.delete_message(self.state.key.chat_id, poll.message_id)

        self.data.current_user = await self.data.user_next(
            self.state.bot,
            self.message.chat.id,
            tuple(self.data.users)[0]
        )

        await self.data.user_remove(self.state)
        await self.state.set_state()

        await self.message.answer(
            _(
                "<b>Игра закончена.</b>\n\n{user} остался последним игроком."
            ).format(
                user=get_username(self.data.current_user)
                ),
            reply_markup=types.ReplyKeyboardRemove()
            )

        self.data = None
