from random import choice
from typing import Callable

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core.filters import BaseFilter
from . import errors
from .data import UnoData
from .data.deck import UnoCard
from .data.deck.colors import UnoColors
from .data.players import UnoPlayer


class UnoFilter(BaseFilter):
    __slots__ = (
        "_is_accepted",
        "answer",
    )

    def __init__(self):
        self._is_accepted: bool = False
        self.answer: str | None = None

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

    async def __call__(self, message: types.Message, state: FSMContext) -> dict | None:
        data_uno = await UnoData.get_data(state)
        player = data_uno.players(message.from_user.id)

        try:
            card = player.get_card(message.sticker)
        except errors.UnoInvalidSticker:
            self.declined = _("What a joke, this card is not from your hand.")

        else:
            self.get_filter_card(data_uno, player)(data_uno, card)
            if self.accepted:
                return {
                    'data_uno': data_uno,
                    'card': card,
                    'answer': self.answer,
                }

        data_uno.players(message.from_user.id).add_card(*data_uno.deck(2))
        await data_uno.set_data(state)

        await message.reply(self.answer.format(user=message.from_user.mention_html()))

    def get_filter_card(self, data: UnoData, player: UnoPlayer) -> Callable[[UnoData, UnoCard], None]:
        match player:
            case data.players.current_player:
                return self.for_current_player

            case _ if len(data.deck) == 1:
                return self.for_start_game

            case data.actions.passed:
                return self.for_passed_player

            case data.actions.skipped:
                return self.for_skipped_player

            case _ if player is data.players[-1]:
                return self.for_prev_player

            case _:
                return self.for_other_player

    def for_current_player(self, data: UnoData, card: UnoCard):
        if data.actions.drawn:
            if data.settings.stacking and card.emoji is data.deck.last_card.emoji:
                self.accepted = choice(
                    (
                        _("{user} doesn't want to take cards."),
                        _("What a heat, +cards to the queue!"),
                    )
                )

            elif not data.settings.stacking:
                self.declined = _("Stacking is not allowed.")

            else:
                self.declined = _("{user}, calm down and take the cards!")

        elif card.color is data.deck.last_card.color:
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

        elif card.emoji is data.deck.last_card.emoji:
            self.accepted = _("{user} changes color!")

        else:
            self.declined = choice(
                (
                    _("{user}, attempt not counted, get a card! =)."),
                    _("Just. Skip. Turn."),
                    _("Someday {user} will be able to make the right turn.")
                )
            )

    def for_start_game(self, data: UnoData, card: UnoCard):
        self.declined = choice(
            (
                _("Hey, the game just started and you're already mistaken!"),
                _("This is not your turn!"),
                _("Hello, mistake at the beginning of the game."),
            )
        )

    def for_passed_player(self, data: UnoData, card: UnoCard):
        if card is data.actions.passed.cards[-1]:
            if (
                    card.emoji is data.deck.last_card.emoji
                    or card.color is data.deck.last_card.color
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

    def for_skipped_player(self, data: UnoData, card: UnoCard):
        if card.emoji is data.deck.last_card.emoji:
            self.accepted = choice(
                (
                    _("{user} is unskippable!"),
                    _("{user}, you can't be skipped!"),
                    _("Skips are not for you =).")
                )
            )

        else:
            self.declined = _("{user}, your turn is skipped =(.")

    def for_prev_player(self, data: UnoData, card: UnoCard):
        if card.emoji is data.deck.last_card.emoji:
            self.accepted = choice(
                (
                    _("{user} keeps throwing cards..."),
                    _("{user}, will anyone stop you?"),
                )
            )

        else:
            self.declined = _("{user}, you have already made your turn.")

    def for_other_player(self, data: UnoData, card: UnoCard):
        if data.settings.jump_in and card == data.deck.last_card:
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
