import asyncio
from dataclasses import dataclass
from random import choice, random, randint

from aiogram import Bot, types, exceptions, enums
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from .. import keyboards
from ..data import UnoData
from ..data.deck import UnoCard
from ..data.deck.colors import UnoColors
from ..data.settings.difficulties import UnoDifficulty
from ..data.settings.modes import UnoMode


@dataclass(slots=True)
class UnoBot:
    message: types.Message
    bot: Bot
    state: FSMContext

    data_uno: UnoData

    def get_cards(self):
        me_data = self.data_uno.players.playing.get(self.bot.id)

        if not me_data:
            return

        for card in me_data.cards:
            filter_card = self.data_uno.filter()
            filter_card.get_filter_card(self.data_uno, self.bot.id)(self.data_uno, card)

            if filter_card.accepted:
                yield card, filter_card.answer

    async def gen_turn(self, timer: TimerTasks, *cards: tuple[UnoCard, str]):
        async with ChatActionSender.choose_sticker(chat_id=self.state.key.chat_id):
            d = self.data_uno.settings.difficulty
            delay = randint(1, 4) * d

            if self.message.chat.type is not enums.ChatType.PRIVATE:
                delay *= 1.5

            await asyncio.sleep(delay)

            del timer[self.state.key]

            if not cards or random() > d / 3 * 1.2:
                await self._proceed_pass(timer)
                return

            card, answer = choice(cards)

            if not self.data_uno.players.current_data.is_me:
                assert not self.message.sticker
                await self.message.delete()

            try:
                self.message = await self.bot.send_sticker(self.state.key.chat_id, card.file_id)
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
            await proceed_turn(self.message, self.bot, self.state, timer, self.data_uno, card, answer)

        except asyncio.CancelledError:
            assert self.message.sticker
            await self.message.delete()

            self.data_uno = await UnoData.get_data(self.state)

            answer = self.data_uno.pick_card(self.message.from_user)

            await self.data_uno.set_data(self.state)
            await self.bot.send_message(self.state.key.chat_id, answer)

    async def _proceed_pass(self, timer: TimerTasks):
        if self.data_uno.state.bluffed:
            # Check if bluffed

            d = self.data_uno.settings.difficulty

            prev_id = self.data_uno.players.by_index(-1)
            prev_data = self.data_uno.players.playing[prev_id]

            if d is UnoDifficulty.HARD:
                d *= len([card for card in prev_data.cards if card.color is self.data_uno.deck[-2].color]) / 4
            else:
                d *= len(prev_data.cards) / 6

            if random() < 1 / (d or 5):
                answer = await self.data_uno.do_bluff(self.bot, self.state.key.chat_id)
            else:
                answer = self.data_uno.do_pass(self.message.from_user)

        else:
            answer = self.data_uno.do_pass(self.message.from_user)

        answer_next = await self.data_uno.do_next(self.bot, self.state)

        try:
            self.message = await self.message.edit_text(f'{answer}\n{answer_next}',
                                                        reply_markup=keyboards.show_cards(False))
        except exceptions.TelegramRetryAfter as retry:
            await asyncio.sleep(retry.retry_after)
            self.message = await retry.method

        from .turn import _update_timer
        await _update_timer(self.message, self.bot, self.state, timer, self.data_uno)

    async def do_seven(self) -> str:
        chosen_id = choice([player[0] for player in self.data_uno.players.playing.items() if not player[1].is_me])
        self.data_uno.do_seven(chosen_id)

        chosen_user = await self.data_uno.players.get_user(self.bot, self.state.key.chat_id, chosen_id)
        return _("I exchange cards with player {chosen_user}.").format(chosen_user=chosen_user.mention_html())

    async def do_color(self) -> str:
        me_data = self.data_uno.players.current_data

        if not me_data.cards:
            color = choice(tuple(UnoColors))

        elif self.data_uno.settings.difficulty is UnoDifficulty.HARD:
            colors = [card.color for card in me_data.cards]
            color = max(set(colors), key=colors.count)

        else:
            color = choice(me_data.cards).color

        self.data_uno.do_color(color)
        return _("I choice {color}.").format(color=color)

    async def gen_uno(self, a: int, b: int):
        try:
            async with ChatActionSender.typing(chat_id=self.state.key.chat_id):
                m = self.data_uno.settings.difficulty / len(self.data_uno.players)
                await asyncio.sleep(randint(a, b) * m)

        except asyncio.CancelledError:
            await self.message.delete_reply_markup()

        else:
            if self.message.entities:  # if user has one card
                user = self.message.from_user
                data_uno = await UnoData.get_data(self.state)

                from .uno import proceed_uno
                await proceed_uno(self.message, self.bot, self.state, data_uno, user)
            else:  # if bot has one card
                await self.message.delete_reply_markup()

    async def gen_poll(self, timer: TimerTasks, player_id: int):
        try:
            await asyncio.sleep(60)
        finally:
            poll = await self.bot.stop_poll(self.state.key.chat_id, self.message.message_id)
            self.data_uno = await UnoData.get_data(self.state)

            if player_id in self.data_uno.players.playing and poll.options[0].voter_count > poll.options[1].voter_count:
                user = await self.data_uno.players.get_user(self.bot, self.state.key.chat_id, player_id)

                from .kick import kick_for_idle
                await kick_for_idle(self.bot, self.state, timer, self.data_uno, user)

                if len(self.data_uno.players) == 1:
                    from .base import finish
                    await finish(self.bot, self.state, timer, self.data_uno)
                elif len(self.data_uno.players.playing) == 1 and self.data_uno.settings.mode is UnoMode.WITH_POINTS:
                    from .base import restart
                    await restart(self.bot, self.state, timer, self.data_uno)

            await self.message.delete()
