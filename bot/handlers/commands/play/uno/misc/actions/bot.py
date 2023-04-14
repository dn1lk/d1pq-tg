import asyncio
from dataclasses import dataclass
from random import choice, random, randint

from aiogram import types, exceptions
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from ..data import UnoData
from ..data.deck import UnoCard
from ..data.deck.colors import UnoColors
from ..data.settings.difficulties import UnoDifficulty

UNO = "UNO!"


@dataclass(slots=True)
class UnoBot:
    message: types.Message
    state: FSMContext
    timer: TimerTasks

    data_uno: UnoData

    def get_cards(self):
        me_player = self.data_uno.players(self.state.bot.id)

        if me_player:
            for card in me_player.cards:
                filter_card = self.data_uno.filter()
                filter_card.get_filter_card(self.data_uno, me_player)(self.data_uno, card)

                if filter_card.accepted:
                    yield card, filter_card.answer

    async def gen_turn(self, cards: tuple[tuple[UnoCard, str]] | None):
        async with ChatActionSender.choose_sticker(chat_id=self.message.chat.id):
            await asyncio.sleep(randint(1, 4) * self.data_uno.settings.difficulty)

            del self.timer[self.state.key]

            if not cards:
                await self._proceed_pass()
                return

            card, answer = choice(cards)

            if not self.data_uno.players.current_player.is_me:
                await self.message.delete()

            try:
                self.message = await self.state.bot.send_sticker(self.state.key.chat_id, card.file_id)
            except exceptions.TelegramRetryAfter as retry:
                await asyncio.sleep(retry.retry_after)
                self.message = await retry.method

        try:
            answer = choice(
                (
                    answer,

                    _("My move is made."),
                    _("Expected? But I don't care."),
                    _("BA-DUM-TSS!"),
                    _(
                        "On a scale of 10, rate the quality of this move.\n"
                        "Where 0 is very good, 10 is excellent."
                    ),
                    _("I still have cards in my hand."),
                    _("Curious, but I know all the hands in the game... I dealt them."),
                    _("Maybe I can even win this game!"),
                    _("Oh, I don't envy the next player..."),
                    _("Br-b. Ah. Yes. No. ..."),
                    _("Oh-oh, this card fell into this chat by itself..."),
                )
            )

            from .turn import proceed_turn
            await proceed_turn(self.message, self.state, self.timer, self.data_uno, card, answer)

        except asyncio.CancelledError:
            self.data_uno = await UnoData.get_data(self.state)

            answer = await self.data_uno.pick_card(
                self.state,
                self.data_uno.players(self.state.key.bot_id)
            )

            await self.data_uno.set_data(self.state)
            await self.message.answer(answer)
            await self.message.delete()

    async def _proceed_pass(self):
        if self.data_uno.actions.bluffed:
            # Check if bluffed

            d = self.data_uno.settings.difficulty

            prev_player = self.data_uno.players[-1]
            prev_card = self.data_uno.deck[-2]

            if d is UnoDifficulty.HARD:
                d *= len([card for card in prev_player.cards if card.color is prev_card.color]) / 4
            else:
                d *= len(prev_player.cards) / 6

            if random() < 1 / (d or 5):
                answer = await self.data_uno.do_bluff(self.state)
            else:
                answer = await self.data_uno.do_pass(self.state)

        else:
            answer = await self.data_uno.do_pass(self.state)

        from .turn import next_turn
        await next_turn(self.message, self.state, self.timer, self.data_uno, answer)

    async def do_color(self) -> str:
        player = self.data_uno.players.current_player
        last_card = self.data_uno.deck.last_card

        if not player.cards:
            color = choice(tuple(UnoColors.exclude(UnoColors.BLACK)))

        elif self.data_uno.settings.difficulty is UnoDifficulty.HARD:
            colors = [card.color for card in player.cards]
            color = max(set(colors), key=colors.count)

        else:
            color = choice(player.cards).color

        self.data_uno.deck[-1] = last_card.replace(color=color)
        return _("I choice {color}.").format(color=color)

    async def do_seven(self) -> str:
        chosen_player = choice([player for player in self.data_uno.players if not player.is_me])
        self.data_uno.do_seven(chosen_player)

        chosen_user = await chosen_player.get_user(self.state.bot, self.state.key.chat_id)
        return _("I exchange cards with player {chosen_user}.").format(chosen_user=chosen_user.mention_html())

    async def gen_uno(self, a: int, b: int):
        try:
            async with ChatActionSender.typing(chat_id=self.message.chat.id):
                m = self.data_uno.settings.difficulty / len(self.data_uno.players)
                await asyncio.sleep(randint(a, b) * m)

        except asyncio.CancelledError:
            await self.message.delete_reply_markup()

        else:
            if self.message.entities:  # if user has one card
                user = await self.state.bot.me()
                data_uno = await UnoData.get_data(self.state)

                from .uno import proceed_uno
                await proceed_uno(self.message, self.state, data_uno, user)
            else:  # if bot has one card
                await self.message.delete_reply_markup()

    async def gen_poll(self):
        try:
            await asyncio.sleep(60)
        finally:
            player = self.data_uno.players.current_player

            poll = await self.state.bot.stop_poll(self.message.chat.id, self.message.message_id)
            data_uno = await UnoData.get_data(self.state)

            if poll.options[0].voter_count > poll.options[1].voter_count and player in data_uno.players:
                user = await player.get_user(self.state.bot, self.state.key.chat_id)

                from .kick import kick_for_idle
                await kick_for_idle(self.message, self.state, self.timer, data_uno, user)

            await self.message.delete()
