import secrets
from dataclasses import dataclass
from typing import Self

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import ngettext as ___

from handlers.commands.play import PlayData
from handlers.commands.play.misc.states import PlayStates
from handlers.commands.play.uno import MIN_PLAYERS
from handlers.commands.play.uno.misc import errors

from .deck import UnoCard, UnoDeck, UnoEmoji
from .deck.colors import UnoColors
from .players import UnoPlayers
from .settings import UnoSettings


@dataclass
class UnoState:
    drawn: int = 0

    passed: bool = False
    skipped: bool = False
    bluffed: bool = False

    color: bool = False
    seven: bool = False


class UnoData(PlayData):
    deck: UnoDeck
    players: UnoPlayers
    settings: UnoSettings

    state: UnoState = UnoState()
    timer_amount: int = 3

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(current_id={self.players.current_id}, last_card={self.deck.last_card}, state={self.state})"

    @property
    def filter(self):  # noqa: ANN201
        from handlers.commands.play.uno.misc.filter import UnoFilter

        return UnoFilter(self)

    def update_turn(self, player_id: int, card: UnoCard) -> None:
        self.deck.last_card = card

        self.players.current_id = player_id
        self.players.current_data.del_card(card)

    async def update_state(self, user: types.User, bot: Bot, chat_id: int) -> formatting.Text | None:
        self.state.passed = self.state.skipped = False

        match self.deck.last_card.emoji:
            case UnoEmoji.NULL if self.settings.seven_0 and self.players.current_data.cards:
                return self.content_null()
            case UnoEmoji.SEVEN if self.settings.seven_0 and self.players.current_data.cards:
                return self.content_seven()
            case UnoEmoji.COLOR | UnoEmoji.DRAW_FOUR:
                return self.content_color()
            case UnoEmoji.DRAW_TWO:
                return self.content_draw(user)
            case UnoEmoji.SKIP:
                return await self.do_skip(bot, chat_id)
            case UnoEmoji.REVERSE:
                return await self.do_reverse(user, bot, chat_id)

    def content_null(self) -> formatting.Text:
        cards_hands = [player_data.cards for player_data in self.players.playing.values()]
        cards_hands.append(cards_hands.pop(0))

        for player_id, cards in zip(self.players.playing, cards_hands, strict=True):
            self.players.playing[player_id].cards = cards

        content = formatting.Text(
            secrets.choice(
                (
                    _("We exchanged cards."),
                    _("Everyone got their neighbor's cards."),
                ),
            ),
        )

        return content

    def content_seven(self) -> formatting.Text | None:
        if len(self.players) == MIN_PLAYERS:
            return self.content_null()

        self.state.seven = True
        raise errors.UnoSeven

    def content_bluff(self) -> formatting.Text:
        self.state.drawn += 4
        self.state.bluffed = True

        content = formatting.Text(
            secrets.choice(
                (
                    _("Is this card legal?"),
                    _("A wild card..."),
                ),
            ),
        )

        return content

    def content_draw(self, user: types.User) -> formatting.Text:
        if self.deck.last_card.emoji == UnoEmoji.DRAW_FOUR:
            _title = self.content_bluff()
        else:
            self.state.bluffed = False
            self.state.drawn += 2

            _title = secrets.choice(
                (
                    _("How cruel!"),
                    _("What a surprise."),
                ),
            )

        _user = formatting.TextMention(user.first_name, user=user)
        content = formatting.Text(
            _title,
            "\n",
            *secrets.choice(
                (
                    (_user, " ", _("is clearly taking revenge... plus")),
                    (_user, " ", _("sends a fiery hello and")),
                ),
            ),
            " ",
            ___("a card.", "{amount} cards.", self.state.drawn).format(amount=self.state.drawn),
        )

        return content

    def content_color(self) -> None:
        self.state.color = True
        raise errors.UnoColor

    def pick_card(self, user: types.User) -> formatting.Text:
        player_data = self.players.playing[user.id]

        if self.state.drawn:
            amount = self.state.drawn
            self.state.drawn = 0
        else:
            amount = 1

        player_data.add_card(*self.deck(amount))

        if player_data.is_me:
            _title = _("I receive")
        else:
            _title = formatting.Text(formatting.TextMention(user.first_name, user=user), " ", _("receives"))

        content = formatting.Text(_title, " ", ___("a card.", "{amount} cards.", amount).format(amount=amount))
        return content

    def do_draw(self, user: types.User) -> formatting.Text:
        self.state.bluffed = False
        return self.pick_card(user)

    def do_pass(self, user: types.User) -> formatting.Text:
        self.state.passed = True
        return self.do_draw(user)

    def do_seven(self, chosen_id: int) -> formatting.Text:
        player_data = self.players.current_data
        chosen_data = self.players.playing[chosen_id]

        player_data.cards, chosen_data.cards = chosen_data.cards, player_data.cards
        self.state.seven = False

        content = formatting.Text(
            secrets.choice(
                (
                    _("Was this choice beneficial? 🤓"),
                    _("The exchange happened!"),
                    _("See don't get confused."),
                ),
            ),
        )

        return content

    def do_color(self, user: types.User, color: UnoColors) -> formatting.Text | None:
        last_card = self.deck.last_card

        self.deck[-1] = last_card.replace(color=color)
        self.state.color = False

        if last_card.emoji is UnoEmoji.DRAW_FOUR:
            return self.content_draw(user)
        return None

    async def do_skip(self, bot: Bot, chat_id: int) -> formatting.Text:
        player_id = self.players.current_id = self.players.by_index(1)
        self.state.skipped = True

        user = await self.players.get_user(bot, chat_id, player_id)
        _user = formatting.TextMention(user.first_name, user=user)

        content = formatting.Text(
            *secrets.choice(
                (
                    (_user, " ", _("loses a turn?")),
                    (_user, " ", _("risks missing a turn.")),
                    (_user, " ", _("can forget about the next turn.")),
                ),
            ),
        )

        return content

    async def do_reverse(self, user: types.User, bot: Bot, chat_id: int) -> formatting.Text:
        if len(self.players) == MIN_PLAYERS:
            return await self.do_skip(bot, chat_id)

        self.players.playing, self.players.current_id = (
            dict(reversed(self.players.playing.items())),
            self.players.current_id,
        )

        content = formatting.Text(
            secrets.choice(
                (
                    _("And vice versa!"),
                    _("A bit of a mess..."),
                ),
            ),
            " ",
            formatting.Bold(formatting.TextMention(user.first_name, user=user), " ", _("changes the queue", ".")),
        )

        return content

    async def do_bluff(self, bot: Bot, chat_id: int) -> formatting.Text:
        player_id = self.players.by_index(-1)
        player_data = self.players.playing[player_id]

        prev_card = self.deck[-2]

        if any(card.color is prev_card.color for card in player_data.cards):
            if player_data.is_me:
                _title = _("Yes, it was a bluff hehe.")
            else:
                _title = _("Bluff! I see suitable cards, not only wilds.")

        else:
            self.state.drawn += 2

            player_id = self.players.current_id
            player_data = self.players.current_data

            if player_data.is_me:
                _title = _("Ah, no. There were no suitable cards. 🙄")
            else:
                _title = secrets.choice(
                    (
                        _("Nope. It is not a bluff."),
                        _("Shhh, this card was legal."),
                        _("This card is suitable."),
                    ),
                )

        user = await self.players.get_user(bot, chat_id, player_id)

        content = formatting.Text(_title, " ", self.do_draw(user))
        return content

    async def do_next(self, bot: Bot, state: FSMContext) -> formatting.Text:
        player_id = self.players.current_id = self.players.by_index(1)
        await self.set_data(state)

        player_data = self.players.current_data

        if player_data.is_me:
            content = formatting.Text(_("My turn."))
        else:
            user = await self.players.get_user(bot, state.key.chat_id, player_id)

            _user = formatting.TextMention(user.first_name, user=user)
            content = formatting.Text(
                *secrets.choice(
                    (
                        (_user, ", ", _("your turn"), "."),
                        (_user, ", ", _("your move"), "."),
                        (_("Now"), " ", _user, " ", _("is moving"), "."),
                        (_("Player's turn"), " ", _user, "."),
                        (_("I pass the turn to"), " ", _user, "."),
                    ),
                ),
            )

        return content

    @classmethod
    async def setup(
        cls,
        bot: Bot,
        state: FSMContext,
        user_ids: list[int],
        settings: UnoSettings,
    ) -> Self:
        await state.set_state(PlayStates.UNO)

        deck = await UnoDeck.setup(bot)
        players = await UnoPlayers.setup(state, deck, user_ids)

        return cls(deck=deck, players=players, settings=settings)

    def restart(self) -> None:
        self.players.restart(self.deck)

        self.deck = UnoDeck(list(self.deck))
        self.state = UnoState()
        self.timer_amount = 3

    async def clear(self, state: FSMContext) -> None:
        await self.players.clear(state)
        await state.clear()
