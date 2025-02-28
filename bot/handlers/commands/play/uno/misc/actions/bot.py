import asyncio
import contextlib
import logging
import secrets
from collections.abc import Generator
from dataclasses import dataclass, replace

from aiogram import Bot, enums, exceptions, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from handlers.commands.play.uno.misc import keyboards
from handlers.commands.play.uno.misc.data import UnoData
from handlers.commands.play.uno.misc.data.deck import UnoCard
from handlers.commands.play.uno.misc.data.deck.colors import UnoColors
from handlers.commands.play.uno.misc.data.settings.difficulties import UnoDifficulty
from handlers.commands.play.uno.misc.data.settings.modes import UnoMode
from utils import TimerTasks

logger = logging.getLogger("bot.uno")


@dataclass(slots=True)
class UnoBot:
    message: types.Message
    bot: Bot
    state: FSMContext

    data_uno: UnoData

    def get_cards(self, me_user: types.User) -> Generator[tuple[UnoCard, formatting.Text], None, None]:
        me_data = self.data_uno.players.playing.get(self.bot.id)

        if not me_data:
            return

        for card in me_data.cards:
            content, accepted = self.data_uno.filter.filter_card(self.bot.id)(me_user, card)
            assert content is not None, "card has no turn reason"

            if accepted:
                yield card, content

    async def gen_turn(self, timer: TimerTasks, *cards: tuple[UnoCard, formatting.Text]) -> None:
        logger.debug("[UNO][bot] turn executing: %s", self.data_uno)

        async with (
            ChatActionSender.choose_sticker(chat_id=self.state.key.chat_id, bot=self.bot),
            timer.lock(self.state.key),
        ):
            difficulty = self.data_uno.settings.difficulty
            delay = (secrets.randbelow(3) + 1) * difficulty * 0.6

            if self.message.chat.type is not enums.ChatType.PRIVATE:
                delay *= 1.5

            await asyncio.sleep(delay)
            del timer[self.state.key]  # cancel current timers

            if not cards or secrets.randbelow(10) / 10 > 1 / difficulty * 1.4:
                await self._proceed_pass(timer)
            else:
                await self._proceed_turn(timer, *cards)

    async def _proceed_turn(self, timer: TimerTasks, *cards: tuple[UnoCard, formatting.Text]) -> None:
        logger.debug("[UNO][bot] turn proceeding: %s", self.data_uno)

        card, content = secrets.choice(cards)

        if not self.data_uno.players.current_data.is_me:
            await self.message.delete()

        try:
            self.message = await self.bot.send_sticker(self.state.key.chat_id, card.file_id)
            content = formatting.Text(
                secrets.choice(
                    (
                        content,
                        _("My move is made."),
                        _("Expected? But I don't care."),
                        _("BA-DUM-TSS!"),
                        _("On a scale of 10, rate the quality of this move.\nWhere 0 is very good, 10 is excellent."),
                        _("I still have cards in my hand."),
                        _("Curious, but I know all the hands in the game... I dealt them."),
                        _("Maybe I can even win this game!"),
                        _("Oh, I don't envy the next player..."),
                        _("Br-b. Ah. Yes. No. ..."),
                        _("Oh-oh, this card fell into this chat by itself..."),
                    ),
                ),
            )

            from .turn import proceed_turn

            await proceed_turn(self.message, self.bot, self.state, timer, self.data_uno, card, content)

        except asyncio.CancelledError:
            if self.message.sticker:
                user = self.message.from_user
                assert user is not None, "wrong user"
                assert user.id == self.bot.id, "user is not bot"

                await self.message.delete()

                data_uno = await UnoData.get_data(self.state)
                if data_uno is None:
                    return

                self.data_uno = data_uno
                content = self.data_uno.pick_card(user)

                await self.data_uno.set_data(self.state)
                await self.bot.send_message(self.state.key.chat_id, **content.as_kwargs())

    async def _proceed_pass(self, timer: TimerTasks):
        logger.debug("[UNO][bot] pass proceeding: %s", self.data_uno)

        user = self.message.from_user
        assert user is not None, "wrong user"

        if self.data_uno.state.bluffed:
            difficulty = self.data_uno.settings.difficulty

            prev_id = self.data_uno.players.by_index(-1)
            prev_data = self.data_uno.players.playing[prev_id]

            if difficulty is UnoDifficulty.HARD:
                difficulty *= len([card for card in prev_data.cards if card.color is self.data_uno.deck[-2].color]) / 4
            else:
                difficulty *= len(prev_data.cards) / 6

            if secrets.randbelow(10) / 10 < 1 / (difficulty or 8):
                content = await self.data_uno.do_bluff(self.bot, self.state.key.chat_id)
            else:
                content = self.data_uno.do_pass(user)
        else:
            content = self.data_uno.do_pass(user)

        content = formatting.Text(content, "\n", await self.data_uno.do_next(self.bot, self.state))
        message = await self.message.edit_text(
            reply_markup=keyboards.show_cards(bluffed=False),
            **content.as_kwargs(),
        )

        assert isinstance(message, types.Message), "wrong message"
        self.message = message

        from .turn import update_timer

        await update_timer(self.message, self.bot, self.state, timer, self.data_uno)

    async def do_seven(self) -> formatting.Text:
        logger.debug("[UNO][bot] seven executing: %s", self.data_uno)

        chosen_id = secrets.choice(
            [player_id for player_id, player_data in self.data_uno.players.playing.items() if not player_data.is_me],
        )
        self.data_uno.do_seven(chosen_id)

        chosen_user = await self.data_uno.players.get_user(self.bot, self.state.key.chat_id, chosen_id)

        content = formatting.Text(
            _("I exchange cards with"),
            " ",
            formatting.TextMention(chosen_user.first_name, user=chosen_user),
        )

        return content

    async def do_color(self) -> formatting.Text:
        logger.debug("[UNO][bot] color executing: %s", self.data_uno)

        me_data = self.data_uno.players.current_data

        if not me_data.cards:
            color = secrets.choice(tuple(UnoColors.exclude(UnoColors.BLACK)))

        elif self.data_uno.settings.difficulty is UnoDifficulty.HARD:
            colors = [card.color for card in me_data.cards if card.color is not UnoColors.BLACK]
            color = max(set(colors), key=colors.count)

        else:
            color = secrets.choice(me_data.cards).color

        content_color = formatting.Text(_("I choice"), " ", formatting.Bold(color))
        content_draw = self.data_uno.do_color(await self.bot.me(), color)

        if content_draw:
            await self.message.answer(**content_color.as_kwargs())
            return content_draw

        return content_color

    async def gen_uno(self, timer: TimerTasks, a: int, b: int) -> None:
        logger.debug("[UNO][bot] uno executing: %s", self.data_uno)

        assert 0 <= a < b, f"wrong values: {a} >= {b}"

        try:
            async with ChatActionSender.typing(chat_id=self.state.key.chat_id, bot=self.bot):
                m = self.data_uno.settings.difficulty / len(self.data_uno.players)
                await asyncio.sleep((secrets.randbelow(b) + a) * m)

                if self.message.entities:  # if user has one card
                    user = await self.bot.me()

                    key = replace(self.state.key, destiny="play:uno:last")
                    async with timer.lock(self.state.key), timer.lock(key):
                        data_uno = await UnoData.get_data(self.state)
                        if data_uno is None:
                            return

                        from .uno import proceed_uno

                        await proceed_uno(self.message, self.bot, self.state, data_uno, user)
        finally:
            # TODO: remove exception
            with contextlib.suppress(exceptions.TelegramBadRequest):
                await self.message.delete_reply_markup()

    async def gen_poll(self, timer: TimerTasks, player_id: int) -> None:
        logger.debug("[UNO][bot] poll executing: %s", self.data_uno)

        try:
            await asyncio.sleep(60)
        finally:
            poll = await self.bot.stop_poll(self.state.key.chat_id, self.message.message_id)

            async with timer.lock(self.state.key):
                data_uno = await UnoData.get_data(self.state)
                if data_uno:
                    self.data_uno = data_uno

                    if (
                        player_id in self.data_uno.players.playing
                        and poll.options[0].voter_count > poll.options[1].voter_count
                    ):
                        user = await self.data_uno.players.get_user(self.bot, self.state.key.chat_id, player_id)

                        from .kick import kick_for_idle

                        await kick_for_idle(self.bot, self.state, timer, self.data_uno, user)

                        if len(self.data_uno.players) == 1:
                            from .base import finish

                            await finish(self.bot, self.state, timer, self.data_uno)
                        elif (
                            len(self.data_uno.players.playing) == 1
                            and self.data_uno.settings.mode is UnoMode.WITH_POINTS
                        ):
                            from .base import restart

                            await restart(self.bot, self.state, timer, self.data_uno)

            await self.message.delete()
