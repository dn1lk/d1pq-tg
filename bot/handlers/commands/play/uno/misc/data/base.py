from dataclasses import dataclass
from random import choice

from aiogram import Bot, types, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers.commands.play import PlayData
from bot.handlers.commands.play.misc.states import PlayStates
from .deck import UnoDeck, UnoCard, UnoEmoji
from .deck.colors import UnoColors
from .players import UnoPlayers
from .settings import UnoSettings
from .. import errors


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

    @classmethod
    def filter(cls):
        from ..filter import UnoFilter
        return UnoFilter()

    def update_turn(self, player_id: int, card: UnoCard):
        self.deck.last_card = card

        self.players.current_id = player_id
        self.players.current_data.del_card(card)

    def update_state(self) -> str | None:
        self.state.passed = self.state.skipped = False

        match self.deck.last_card.emoji:
            case UnoEmoji.NULL if self.settings.seven_0 and self.players.current_data.cards:
                return self.answer_null()

            case UnoEmoji.SEVEN if self.settings.seven_0 and self.players.current_data.cards:
                return self.answer_seven()

            case UnoEmoji.COLOR | UnoEmoji.DRAW_FOUR:
                return self.answer_color()

            case UnoEmoji.DRAW_TWO:
                return self.answer_draw()

            case UnoEmoji.SKIP:
                return self.answer_skip()

            case UnoEmoji.REVERSE:
                return self.answer_reverse()

    def answer_null(self) -> str:
        cards_hands = [player_data.cards for player_data in self.players.playing.values()]
        cards_hands.append(cards_hands.pop(0))

        for player_id, cards in zip(self.players.playing, cards_hands):
            self.players.playing[player_id].cards = cards

        return choice(
            (
                _("We exchanged cards."),
                _("Everyone got their neighbor's cards.")
            )
        )

    def answer_seven(self) -> str | None:
        if len(self.players) == 2:
            return self.answer_null()

        self.state.seven = True
        raise errors.UnoSeven()

    def answer_bluff(self) -> str:
        self.state.drawn += 4
        self.state.bluffed = True

        return choice(
            (
                _("Is this card legal?"),
                _("A wild card..."),
            )
        )

    def answer_draw(self) -> str:
        if self.deck.last_card.emoji == UnoEmoji.DRAW_FOUR:
            answer_one = self.answer_bluff()
        else:
            self.state.drawn += 2

            answer_one = choice(
                (
                    _("How cruel!"),
                    _("What a surprise."),
                )
            )

        answer_two = choice(
            (
                _("{user} is clearly taking revenge... plus"),
                _("{user} sends a fiery hello and"),
            )
        )

        answer_three = ___("a card.", "{amount} cards.", self.state.drawn).format(amount=self.state.drawn)

        return f'{answer_one}\n{answer_two} {answer_three}'

    def answer_color(self):
        self.state.color = True
        raise errors.UnoColor()

    def answer_skip(self) -> str:
        self.players.current_id = self.players.by_index(1)
        self.state.skipped = True

        return choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
                _("{user} can forget about the next turn."),
            )
        )

    def answer_reverse(self) -> str:
        if len(self.players) == 2:
            return self.answer_skip()

        self.players.playing, self.players.current_id = (
            dict(reversed(self.players.playing.items())), self.players.current_id
        )

        answer_one = choice(
            (
                _("And vice versa!"),
                _("A bit of a mess..."),
            )
        )

        answer_two = _("{user} changes the queue.")

        return f'{answer_one} {html.bold(answer_two)}'

    def pick_card(self, user: types.User) -> str:
        player_data = self.players.playing[user.id]

        if self.state.drawn:
            amount = self.state.drawn
            self.state.drawn = 0
        else:
            amount = 1

        player_data.add_card(*self.deck(amount))

        if player_data.is_me:
            answer_one = _("I receive")
        else:
            answer_one = _("{user} receives").format(user=user.mention_html())

        answer_two = ___("a card.", "{amount} cards.", amount).format(amount=amount)

        return f"{answer_one} {answer_two}"

    def do_draw(self, user: types.User) -> str:
        self.state.bluffed = False
        return self.pick_card(user)

    async def do_bluff(self, bot: Bot, chat_id: int) -> str:
        player_id = self.players.by_index(-1)
        player_data = self.players.playing[player_id]

        prev_card = self.deck[-2]

        if any(card.color is prev_card.color for card in player_data.cards):
            if player_data.is_me:
                answer = _("Yes, it was a bluff hehe.")
            else:
                answer = _("Bluff! I see suitable cards, not only wilds.")

        else:
            self.state.drawn += 2

            player_id = self.players.current_id
            player_data = self.players.current_data

            if player_data.is_me:
                answer = _("Ah, no. There were no suitable cards =(")
            else:
                answer = choice(
                    (
                        _("Nope. It is not a bluff."),
                        _("Shhh, this card was legal."),
                        _("This card is suitable.")
                    )
                )

        user = await self.players.get_user(bot, chat_id, player_id)
        return f'{answer} {self.do_draw(user)}'

    def do_pass(self, user: types.User) -> str:
        self.state.passed = True
        return self.do_draw(user)

    def do_seven(self, chosen_id: int) -> str:
        player_data = self.players.current_data
        chosen_data = self.players.playing[chosen_id]

        player_data.cards, chosen_data.cards = chosen_data.cards, player_data.cards
        self.state.seven = False

        return choice(
            (
                _("Was this choice beneficial? =)"),
                _("The exchange happened!"),
                _("See don't get confused."),
            )
        )

    def do_color(self, color: UnoColors) -> str | None:
        last_card = self.deck.last_card

        self.deck[-1] = last_card.replace(color=color)
        self.state.color = False

        if last_card.emoji is UnoEmoji.DRAW_FOUR:
            return self.answer_draw()

    async def do_next(self, bot: Bot, state: FSMContext) -> str:
        player_id = self.players.current_id = self.players.by_index(1)
        await self.set_data(state)

        player_data = self.players.current_data

        if player_data.is_me:
            answer = _("My turn.")
        else:
            user = await self.players.get_user(bot, state.key.chat_id, player_id)
            answer = choice(
                (
                    _("{user}, your turn."),
                    _("{user}, your move."),
                    _("Now {user} is moving."),
                    _("Player's turn {user}."),
                    _("I pass the turn to the player {user}."),
                )
            ).format(user=user.mention_html())

        return answer

    @classmethod
    async def setup(
            cls,
            bot: Bot,
            state: FSMContext,
            user_ids: list[int],
            settings: UnoSettings,
    ) -> "UnoData":
        await state.set_state(PlayStates.UNO)

        deck = await UnoDeck.setup(bot)
        players = await UnoPlayers.setup(bot, state, deck, user_ids)

        return cls(deck=deck, players=players, settings=settings)

    def restart(self):
        self.players.restart(self.deck)

        self.deck = UnoDeck(list(self.deck))
        self.state = UnoState()
        self.timer_amount = 3

    async def clear(self, bot: Bot, state: FSMContext):
        await self.players.clear(bot, state)
        await state.clear()
