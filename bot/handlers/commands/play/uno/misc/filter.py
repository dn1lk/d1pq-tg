from dataclasses import dataclass
from random import choice
from typing import Callable

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.filters import BaseFilter
from bot.core.utils import TimerTasks
from . import errors
from .data import UnoData
from .data.deck import UnoCard, UnoEmoji
from .data.deck.colors import UnoColors


@dataclass(slots=True)
class UnoFilter(BaseFilter):
    _action: str

    _is_accepted: bool = False
    answer: str = None

    @property
    def accepted(self):
        return self._is_accepted

    @accepted.setter
    def accepted(self, answer: str):
        self._is_accepted = True
        self.answer = answer

    @property
    def declined(self):
        return not self._is_accepted

    @declined.setter
    def declined(self, answer: str):
        self._is_accepted = False
        self.answer = answer

    async def __call__(self, event: types.Message | types.CallbackQuery, bot: Bot, state: FSMContext):
        data_uno = await UnoData.get_data(state)

        match self._action:
            case 'turn':
                return await self.for_turn(event, state, data_uno)
            case 'pass':
                return await self.for_pass(event, bot, state, data_uno)
            case 'bluff':
                return await self.for_bluff(event, bot, state, data_uno)
            case 'color':
                return await self.for_color(event, data_uno)
            case 'uno':
                return await self.for_uno(event, state, data_uno)

    async def for_turn(self, message: types.Message, state: FSMContext, data_uno: UnoData) -> dict | None:
        player_id = message.from_user.id
        player_data = data_uno.players.playing[player_id]

        try:
            card = player_data.get_card(message.sticker)

        except errors.UnoInvalidSticker:
            self.declined = _("What a joke, this card is not from your hand.")

        else:
            self.get_filter_card(data_uno, player_id)(data_uno, card)
            if self.accepted:
                return {
                    'card': card,
                    'answer': self.answer,
                }

        player_data.add_card(*data_uno.deck(2))
        await data_uno.set_data(state)

        await message.reply(self.answer.format(user=message.from_user.mention_html()))

    def get_filter_card(self, data_uno: UnoData, player_id: int) -> Callable[[UnoData, UnoCard], None]:
        if player_id == data_uno.players.current_id:
            return self._for_current_player

        elif len(data_uno.deck) == 1:
            return self._for_start_game

        else:
            if player_id == data_uno.players.by_index(-1):

                if data_uno.state.passed:
                    return self._for_passed_player
                if data_uno.state.skipped:
                    return self._for_skipped_player
                else:
                    return self._for_prev_player

            else:
                return self._for_other_player

    def _for_current_player(self, data_uno: UnoData, card: UnoCard):
        if data_uno.state.drawn:
            if data_uno.settings.stacking and (
                    card.emoji is data_uno.deck.last_card.emoji
                    or card.emoji is UnoEmoji.DRAW_TWO and card.color is data_uno.deck.last_card.color
            ):
                self.accepted = choice(
                    (
                        _("{user} doesn't want to take cards."),
                        _("What a heat, +cards to the queue!"),
                    )
                )

            elif not data_uno.settings.stacking:
                self.declined = _("Stacking is not allowed.")

            else:
                self.declined = _("{user}, calm down and take the cards!")

        elif card.color is data_uno.deck.last_card.color:
            if card.color is UnoColors.BLACK:
                self.accepted = _("Another black card???")

            else:
                self.accepted = choice(
                    (
                        _("So... {user}."),
                        _("Again {color}...").format(color=card.color),
                        _("Wow, you got {color}!").format(color=card.color),
                    )
                )

        elif card.color is UnoColors.BLACK:
            self.accepted = _("Black card by {user}!")

        elif card.emoji is data_uno.deck.last_card.emoji:
            self.accepted = _("{user} changes color!")

        else:
            self.declined = choice(
                (
                    _("{user}, attempt not counted, get a card! 🧐"),
                    _("Just. Skip. Turn."),
                    _("Someday {user} will be able to make the right turn.")
                )
            )

    def _for_start_game(self, __: UnoData, ___: UnoCard):
        self.declined = choice(
            (
                _("Hey, the game just started and you're already mistaken!"),
                _("This is not your turn!"),
                _("Hello, mistake at the beginning of the game."),
            )
        )

    def _for_passed_player(self, data_uno: UnoData, card: UnoCard):
        if card is data_uno.players.playing[data_uno.players.by_index(-1)].cards[-1]:
            # If is received card

            if (
                    card.emoji is data_uno.deck.last_card.emoji
                    or card.color is data_uno.deck.last_card.color
                    or card.color is UnoColors.BLACK
            ):
                self.accepted = choice(
                    (
                        _("{user}, you're in luck!"),
                        _("{user}, is that honest?"),
                    )
                )

            else:
                self.declined = _("No, this card is wrong. Take another one!")
        else:
            self.declined = choice(
                (
                    _("This is not your last card!"),
                    _("This is not that card."),
                    _("I mixed you another card!"),
                )
            )

    def _for_skipped_player(self, data_uno: UnoData, card: UnoCard):
        if card.emoji is data_uno.deck.last_card.emoji:
            self.accepted = choice(
                (
                    _("{user} is unskippable!"),
                    _("{user}, you can't be skipped!"),
                    _("Skips are not for you. 😎")
                )
            )

        else:
            self.declined = _("{user}, your turn is skipped. 🤨")

    def _for_prev_player(self, data_uno: UnoData, card: UnoCard):
        if card.emoji in (UnoEmoji.DRAW_TWO, UnoEmoji.DRAW_FOUR):
            self.declined = choice(
                (
                    _("This card cannot be played consecutively."),
                    _("These cards cannot be stacked."),
                    _("Yeah, what if we all put all our cards?"),
                )
            )

        elif card.emoji is data_uno.deck.last_card.emoji:
            self.accepted = choice(
                (
                    _("{user} keeps throwing cards..."),
                    _("{user}, will anyone stop you?"),
                )
            )

        else:
            self.declined = _("{user}, you have already made your turn.")

    def _for_other_player(self, data_uno: UnoData, card: UnoCard):
        if data_uno.settings.jump_in and card == data_uno.deck.last_card:
            self.accepted = choice(
                (
                    _("We've been interrupted!"),
                    _("I bet {user} will win this game!"),
                    _("Suddenly, {user}."),
                )
            )

        else:
            self.declined = choice(
                (
                    _("Hold your horses, {user}. Now is not your turn."),
                    _("Hey, {user}. Your card doesn't belong this turn."),
                    _("No. No no no. No. Again, NO!"),
                    _("Someone explain to {user} how to play."),
                    _("Can I just give {user} a card and we'll pretend like nothing happened?"),
                    _("I'm betting on {user}'s defeat."),
                )
            )

    @staticmethod
    async def for_bluff(query: types.CallbackQuery, bot: Bot, state: FSMContext, data_uno: UnoData) -> bool | None:
        current_id = data_uno.players.current_id

        if query.from_user.id == current_id:
            return True

        else:
            user = await data_uno.players.get_user(bot, state.key.chat_id, current_id)
            answer = _("Only {user} can do that.").format(user=user.first_name)

            await query.answer(answer)

    @staticmethod
    async def for_color(query: types.CallbackQuery, data_uno: UnoData) -> bool | None:
        current_id = data_uno.players.current_id

        if query.from_user.id == current_id:
            return True

        await query.answer(_("Nice try."))

    @staticmethod
    async def for_uno(query: types.CallbackQuery, state: FSMContext, data_uno: UnoData) -> bool | None:
        if query.from_user.id in data_uno.players.playing:
            timer_uno = TimerTasks('say_uno')

            if any(timer_uno[state.key]):
                await query.answer(_("Next time be faster!"))
            else:
                return True

        else:
            await query.answer(_("You are not in the game!"))

    @staticmethod
    async def for_pass(message: types.Message, bot: Bot, state: FSMContext, data_uno: UnoData) -> bool | None:
        current_id = data_uno.players.current_id

        if message.from_user.id == current_id:
            return True

        user = await data_uno.players.get_user(bot, state.key.chat_id, current_id)
        await message.reply(
            _(
                "Of course, I don't mind, but now it's {user}'s turn.\n"
                "We'll have to wait. 🫠"
            ).format(user=user.mention_html())
        )
