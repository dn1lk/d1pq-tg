import secrets
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any, Literal

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import TimerTasks

from . import errors
from .data import UnoData
from .data.deck import UnoCard, UnoEmoji
from .data.deck.colors import UnoColors


@dataclass(slots=True)
class UnoFilter:
    data: UnoData

    async def for_turn(self, message: types.Message, state: FSMContext, timer: TimerTasks) -> dict | Literal[False]:
        assert message.from_user is not None, "wrong user"
        assert message.sticker is not None, "wrong sticker"

        if len(self.data.players) <= 1:
            content = formatting.Text(_("Who are you playing with?"))
            await message.reply(**content.as_kwargs())
            return False

        player_id = message.from_user.id
        player_data = self.data.players.playing[player_id]

        try:
            card = player_data.get_card(message.sticker)
        except errors.UnoInvalidSticker:
            content = formatting.Text(_("What a joke, this card is not from your hand."))
        else:
            content, accepted = self.filter_card(player_id)(message.from_user, card)
            if accepted:
                del timer[state.key]
                return {
                    "card": card,
                    "content": content,
                }

        player_data.add_card(*self.data.deck(2))
        await self.data.set_data(state)

        await message.reply(**content.as_kwargs())
        return False

    def filter_card(self, player_id: int) -> Callable[[types.User, UnoCard], tuple[formatting.Text, bool]]:
        if player_id == self.data.players.current_id:
            func = self._for_current_player

        elif len(self.data.deck) == 1:
            func = self._for_start_game

        elif player_id == self.data.players.by_index(-1):
            if self.data.state.passed:
                func = self._for_passed_player
            elif self.data.state.skipped:
                func = self._for_skipped_player
            else:
                func = self._for_prev_player

        else:
            func = self._for_other_player

        return func

    def _for_current_player(self, user: types.User, card: UnoCard) -> tuple[formatting.Text, bool]:
        content, accepted = formatting.Text(), False
        _user = formatting.TextMention(user.first_name, user=user)

        if self.data.state.drawn:
            if self.data.settings.stacking and (
                card.emoji is self.data.deck.last_card.emoji
                or card.emoji is UnoEmoji.DRAW_TWO
                and card.color is self.data.deck.last_card.color
            ):
                accepted = True
                content = formatting.Text(
                    *secrets.choice(
                        (
                            (_user, " ", _("doesn't want to take cards"), "."),
                            (_("What a heat, +cards to the queue!"),),
                        ),
                    ),
                )

            elif not self.data.settings.stacking:
                content = formatting.Text(_("Stacking is not allowed."))

            else:
                content = formatting.Text(_user, ", ", _("calm down and take the cards"), "!")

        elif card.color is self.data.deck.last_card.color:
            accepted = True

            if card.color is UnoColors.BLACK:
                content = formatting.Text(_("Another black card???"))

            else:
                content = formatting.Text(
                    *secrets.choice(
                        (
                            (_("So"), "... ", _user, "."),
                            (_("Again {color}...").format(color=card.color),),
                            (_("Wow, you got {color}!").format(color=card.color),),
                        ),
                    ),
                )

        elif card.color is UnoColors.BLACK:
            accepted = True
            content = formatting.Text(_("Black card by"), " ", _user, "!")

        elif card.emoji is self.data.deck.last_card.emoji:
            accepted = True
            content = formatting.Text(_user, " ", _("changes color"), "!")

        else:
            content = formatting.Text(
                *secrets.choice(
                    (
                        (_user, ", ", _("attempt not counted, get a card! 🧐")),
                        (_("Just. Skip. Turn."),),
                        (_("Someday"), " ", _user, " ", _("will be able to make the right turn"), "."),
                    ),
                ),
            )

        return content, accepted

    def _for_start_game(self, *__: Any) -> tuple[formatting.Text, bool]:
        content = formatting.Text(
            secrets.choice(
                (
                    _("Hey, the game just started and you're already mistaken!"),
                    _("This is not your turn!"),
                    _("Hello, mistake at the beginning of the game."),
                ),
            ),
        )

        return content, False

    def _for_passed_player(self, user: types.User, card: UnoCard) -> tuple[formatting.Text, bool]:
        content, accepted = formatting.Text(), False
        _user = formatting.TextMention(user.first_name, user=user)

        if card is self.data.players.playing[self.data.players.by_index(-1)].cards[-1]:
            # If is received card

            if (
                card.emoji is self.data.deck.last_card.emoji
                or card.color is self.data.deck.last_card.color
                or card.color is UnoColors.BLACK
            ):
                accepted = True
                content = formatting.Text(
                    *secrets.choice(
                        (
                            (_user, ", ", _("you're in luck!")),
                            (_user, ", ", _("is that honest?")),
                        ),
                    ),
                )

            else:
                content = formatting.Text(_("No, this card is wrong. Take another one!"))
        else:
            content = formatting.Text(
                secrets.choice(
                    (
                        _("This is not your last card!"),
                        _("This is not that card."),
                        _("I mixed you another card!"),
                    ),
                ),
            )

        return content, accepted

    def _for_skipped_player(self, user: types.User, card: UnoCard) -> tuple[formatting.Text, bool]:
        content, accepted = formatting.Text(), False
        _user = formatting.TextMention(user.first_name, user=user)

        if card.emoji is self.data.deck.last_card.emoji:
            accepted = True
            content = formatting.Text(
                *secrets.choice(
                    (
                        (_user, " ", _("is unskippable!")),
                        (_user, " ", _("you can't be skipped!")),
                        (_("Skips are not for you. 😎"),),
                    ),
                ),
            )
        else:
            content = formatting.Text(_user, ", ", _("your turn is skipped. 🤨"))

        return content, accepted

    def _for_prev_player(self, user: types.User, card: UnoCard) -> tuple[formatting.Text, bool]:
        content, accepted = formatting.Text(), False
        _user = formatting.TextMention(user.first_name, user=user)

        if card.emoji in (UnoEmoji.DRAW_TWO, UnoEmoji.DRAW_FOUR):
            content = formatting.Text(
                secrets.choice(
                    (
                        _("This card cannot be played consecutively."),
                        _("These cards cannot be stacked."),
                        _("Yeah, what if we all put all our cards?"),
                    ),
                ),
            )

        elif card.emoji is self.data.deck.last_card.emoji:
            accepted = True
            content = formatting.Text(
                *secrets.choice(
                    (
                        (_user, " ", _("keeps throwing cards...")),
                        (_user, ", ", _("will anyone stop you?")),
                    ),
                ),
            )

        else:
            content = formatting.Text(_user, ", ", _("you have already made your turn"), ".")

        return content, accepted

    def _for_other_player(self, user: types.User, card: UnoCard) -> tuple[formatting.Text, bool]:
        content, accepted = formatting.Text(), False
        _user = formatting.TextMention(user.first_name, user=user)

        if self.data.settings.jump_in and card == self.data.deck.last_card:
            accepted = True
            content = formatting.Text(
                *secrets.choice(
                    (
                        (_("We've been interrupted!"),),
                        (_("I bet"), " ", _user, " ", _("will win this game"), "!"),
                        (_("Suddenly"), ", ", _user, "."),
                    ),
                ),
            )

        else:
            content = formatting.Text(
                *secrets.choice(
                    (
                        (_("Hold your horses"), ", ", _user, ". ", _("Now is not your turn.")),
                        (
                            _("Hey", ", ", _user, ". ", _("Your card doesn't belong this turn.")),
                            (_("No. No no no. No. Again, NO!"),),
                            (_("Someone explain to"), " ", _user, _("how to play"), "."),
                            (_("Can I just give"), " ", _user, " ", "a card and we'll pretend like nothing happened"),
                            "?",
                        ),
                        (_("I'm betting on defeat of"), " ", _user, "."),
                    ),
                ),
            )

        return content, accepted

    async def for_pass(self, message: types.Message, bot: Bot, state: FSMContext, timer: TimerTasks) -> bool:
        assert message.from_user is not None, "wrong user"

        current_id = self.data.players.current_id

        if message.from_user.id == current_id:
            del timer[state.key]
            return True

        user = await self.data.players.get_user(bot, state.key.chat_id, current_id)

        content = formatting.Text(
            _("Of course, I don't mind, but now it's turn of"),
            " ",
            formatting.TextMention(user.first_name, user=user),
            "\n",
            _("We'll have to wait. 🙂"),
        )

        await message.reply(**content.as_kwargs())
        return False

    async def for_bluff(self, query: types.CallbackQuery, bot: Bot, state: FSMContext, timer: TimerTasks) -> bool:
        current_id = self.data.players.current_id

        if query.from_user.id == current_id:
            del timer[state.key]
            return True

        user = await self.data.players.get_user(bot, state.key.chat_id, current_id)
        text = _("Only {user} can do that.").format(user=formatting.BlockQuote(user.first_name).as_markdown())

        await query.answer(text)
        return False

    async def for_color(self, query: types.CallbackQuery, state: FSMContext, timer: TimerTasks) -> bool:
        current_id = self.data.players.current_id

        if query.from_user.id == current_id:
            del timer[state.key]
            return True

        await query.answer(_("Nice try."))
        return False

    async def _for_seven_player(self, message: types.Message, bot: Bot, state: FSMContext) -> types.User | None:
        assert message.entities is not None, "wrong entities"
        if message.entities[0].user:
            chosen_user = message.entities[0].user

            if chosen_user.id in self.data.players.playing:
                return chosen_user
        else:
            assert message.text is not None, "wrong text"

            for player_id in self.data.players.playing:
                chosen_user = await self.data.players.get_user(bot, state.key.chat_id, player_id)

                if f"@{chosen_user.username}" in message.text:
                    return chosen_user

        return None

    async def for_seven(
        self,
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
    ) -> dict | Literal[False]:
        assert message.from_user is not None, "wrong user"

        current_id = self.data.players.current_id

        if message.from_user.id == current_id:
            chosen_user = await self._for_seven_player(message, bot, state)
            if chosen_user:
                del timer[state.key]
                return {
                    "chosen_id": chosen_user.id,
                }

            content = formatting.Text(_("Chosen user is not playing with us."))
        else:
            user = await self.data.players.get_user(bot, state.key.chat_id, current_id)
            content = formatting.Text(
                _("Only"),
                " ",
                formatting.TextMention(user.first_name, user=user),
                _("can choose with whom to exchange cards"),
                ".",
            )

        await message.answer(**content.as_kwargs())
        return False

    async def for_uno(self, query: types.CallbackQuery, state: FSMContext, timer: TimerTasks) -> bool:
        key = replace(state.key, destiny="play:uno:last")
        async with timer.lock(key):
            if query.from_user.id in self.data.players.playing:
                if any(timer[key]):
                    del timer[key]
                    return True

                await query.answer(_("Next time be faster!"))
            else:
                await query.answer(_("You are not in the game!"))

            return False
