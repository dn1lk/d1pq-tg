import asyncio
from random import choice
from typing import Optional

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
        self.message = message
        self.state = state

        self.data = data

        from .bot import UnoBot

        self.bot = UnoBot(self.message, self.state.bot, self.data)

        print(self.data.users.keys(), self.data.current_user.first_name, self.data.current_card, self.data.current_special, self.data.kick_polls.keys())

    async def prepare(self, card: UnoCard, accept: str):
        try:
            await self.data.update_current_card(card)

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

            await self.data.remove_user(self.state)

        await self.process(accept)

    async def uno(self):
        self.data.uno_users_id.append(self.data.current_user.id)

        if self.data.current_user.id == self.state.bot.id:
            asyncio.create_task(
                self.bot.uno(),
                name=self.bot.task_name + ':uno'
            )

            await self.message.answer(
                _("У меня осталась одна карта!"),
                reply_markup=k.game_uno_uno(),
            )
        else:
            await self.message.answer(
                _("У игрока {user} осталась одна карта!").format(user=get_username(self.data.current_user)),
                reply_markup=k.game_uno_uno(),
            )

    async def process(self, accept: str):
        answer = await self.data.special_card(self.state.bot, self.message.chat) or accept

        if self.data.current_special.draw and not self.data.current_card.special.draw:
            await self.message.answer(
                await self.data.add_card(
                    self.state.bot,
                    self.data.current_special.draw.user,
                    self.data.current_special.draw.amount
                )
            )

            self.data.current_special.draw = None

        await self.next(answer)

    async def next(self, answer: str):
        if self.data.current_special.color:
            if self.message.from_user.id == self.state.bot.id:
                answer = await self.bot.get_color()
            else:
                return await self.message.answer(
                    answer,
                    reply_markup=k.game_uno_color()
                )

        await self.move(answer)

    async def move(self, answer: Optional[str] = ""):
        self.data.current_user = await self.data.next_user(self.state.bot, self.message.chat.id)
        print(self.data.current_user.first_name)
        if self.data.current_user.id == self.state.bot.id or \
                self.data.current_card in self.data.users[self.state.bot.id]:
            if self.data.current_card in self.data.users[self.state.bot.id]:
                await asyncio.sleep(choice(range(5)))

            print(1, self.data.current_user.first_name, self.data.current_card)
            asyncio.create_task(self.bot.gen(self.state), name=self.bot.task_name)
            print(1, self.data.current_user.first_name, self.data.current_card)
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
                ).format(user=get_username(self.data.current_user)),
                reply_markup=k.game_uno_show_cards()
            )

        from .. import timer, uno_timeout

        timer(self.state, uno_timeout, message=self.message, data_uno=self.data)

    async def end(self):
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and 'uno' in task.get_name():
                task.cancel()

        for poll in self.data.kick_polls.values():
            await self.state.bot.delete_message(self.state.key.chat_id, poll.message_id)

        self.data.current_user = (
            await self.state.bot.get_chat_member(self.state.key.chat_id, tuple(self.data.users)[0])
        ).user

        await self.data.remove_user(self.state)
        await self.state.set_state()

        await self.message.answer(
            _(
                "<b>Игра закончена.</b>\n\n{user} остался последним игроком."
            ).format(
                user=get_username(self.data.current_user)
            )
        )

        self.data = None
