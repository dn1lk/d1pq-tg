from dataclasses import dataclass
from random import choice

from aiogram import html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, ngettext as ___

from bot.handlers.commands.play import PlayData
from bot.handlers.commands.play.misc.states import PlayStates
from .deck import UnoDeck, UnoCard, UnoEmoji
from .deck.colors import UnoColors
from .players import UnoPlayers, UnoPlayer
from .settings import UnoSettings
from .settings.modes import UnoMode
from .. import errors


@dataclass
class UnoActions:
    drawn: int = 0

    passed: UnoPlayer = None
    skipped: UnoPlayer = None
    bluffed: UnoPlayer = None

    uno: UnoPlayer = None

    color: UnoPlayer = None
    seven: UnoPlayer = None


class UnoData(PlayData):
    deck: UnoDeck
    players: UnoPlayers
    settings: UnoSettings

    actions: UnoActions = UnoActions()
    timer_amount: int = 3

    @classmethod
    def filter(cls):
        from ..filter import UnoFilter
        return UnoFilter()

    async def update_turn(self, state: FSMContext, user_id: int, card: UnoCard):
        self.players.current_player = current_player = self.players[user_id]
        self.deck.last_card = card
        current_player.remove_card(card)

        if len(current_player.cards) == 1:
            self.actions.uno = current_player
            raise errors.UnoOneCard()

        if len(current_player.cards) == 0:
            self.update_action()

            if self.actions.drawn:
                self.players.current_player = self.players >> 1
                await self.do_draw(state)

            if self.settings.mode is UnoMode.WITH_POINTS:
                self.restart()

                raise errors.UnoRestart()
            if len(self.players) == 2:
                await self.clear(state)

                raise errors.UnoEnd()

            self.players.finish_player(self.deck, current_player)
            raise errors.UnoNoCards()

    def update_action(self) -> str | None:
        self.actions.passed = self.actions.skipped = self.actions.uno = None

        match self.deck.last_card.emoji:
            case UnoEmoji.NULL if self.settings.seven_0 and self.players.current_player.cards:
                return self.answer_null()

            case UnoEmoji.SEVEN if self.settings.seven_0 and self.players.current_player.cards:
                return self.answer_seven()

            case _ if self.deck.last_card.color is UnoColors.BLACK:
                return self.answer_color()

            case UnoEmoji.DRAW_TWO | UnoEmoji.DRAW_FOUR:
                return self.answer_draw()

            case UnoEmoji.REVERSE:
                return self.answer_reverse()

            case UnoEmoji.SKIP:
                return self.answer_skip()

    def answer_null(self) -> str:
        cards_hands = [player.cards for player in self.players]
        cards_hands.append(cards_hands.pop(0))

        for player, cards in zip(self.players, cards_hands):
            player.cards = cards

        answer = _("We have exchanged cards with next neighbors!")

        return answer

    def answer_seven(self) -> str | None:
        self.actions.seven = self.players.current_player

        if len(self.players) == 2:
            return self.answer_null()

        raise errors.UnoSeven()

    def answer_bluff(self) -> str:
        self.actions.bluffed = self.players.current_player
        self.actions.drawn += 4

        answer = choice(
            (
                _("Is this card legal?"),
                _("A wild card..."),
            )
        )

        return answer

    def answer_draw(self) -> str:
        if self.deck.last_card.emoji == UnoEmoji.DRAW_FOUR:
            answer_one = self.answer_bluff()
        else:
            self.actions.drawn += 2

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

        answer_three = ___("a card.", "{amount} cards.", self.actions.drawn).format(amount=self.actions.drawn)

        return f'{answer_one}\n{answer_two} {answer_three}'

    def answer_color(self):
        self.actions.color = self.players.current_player
        raise errors.UnoColor()

    def answer_reverse(self) -> str:
        if len(self.players) == 2:
            return self.answer_skip()

        self.players._players_in, self.players.current_player = reversed(self.players), self.players.current_player

        answer_one = choice(
            (
                _("And vice versa!"),
                _("A bit of a mess..."),
            )
        )

        answer_two = _("{user} changes the queue.")

        return f'{answer_one} {html.bold(answer_two)}'

    def answer_skip(self) -> str:
        self.actions.skipped = self.players.current_player
        self.players.current_player = self.players >> 1

        answer = choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
                _("{user} can forget about the next turn."),
            )
        )

        return answer

    async def pick_card(self, state: FSMContext, player: UnoPlayer = None) -> str:
        if not player:
            player = self.players.current_player

        if self.actions.drawn == 0:
            self.actions.drawn = 1

        if player.is_me:
            answer_one = _("I receive")
        else:
            user = await player.get_user(state.bot, state.key.chat_id)
            answer_one = _("{user} receives").format(user=user.mention_html())

        answer_two = ___("a card.", "{amount} cards.", self.actions.drawn).format(amount=self.actions.drawn)

        player.add_card(*self.deck[self.actions.drawn])
        self.actions.drawn = 0

        return f"{answer_one} {answer_two}"

    def do_seven(self, chosen_player: UnoPlayer):
        player = self.players.current_player
        player.cards, chosen_player.cards = chosen_player.cards, player.cards

    async def do_bluff(self, state: FSMContext) -> str:
        prev_card = self.deck.last_card
        player = self.actions.bluffed

        if any(card.color is prev_card.color for card in player.cards):
            if player.is_me:
                answer = _("Yes, it was a bluff hehe.")
            else:
                answer = _("Bluff! I see suitable cards, not only wilds.")

        else:
            player = self.players.current_player
            self.actions.drawn += 2

            if player.is_me:
                answer = _("Ah, no. There were no suitable cards =(")
            else:
                answer = choice(
                    (
                        _("Nope. It is not a bluff."),
                        _("Shhh, this card was legal."),
                        _("This card is suitable.")
                    )
                )

        return f'{answer} {await self.do_draw(state, player)}'

    async def do_draw(self, state: FSMContext, player: UnoPlayer = None) -> str:
        answer = await self.pick_card(state, player)
        self.actions.bluffed = None

        return answer

    async def do_pass(self, state: FSMContext) -> str:
        answer = await self.do_draw(state)
        self.actions.passed = self.players.current_player

        return answer

    async def do_next(self, state: FSMContext) -> str:
        self.players.current_player = player = self.players >> 1
        await self.set_data(state)

        if player.is_me:
            answer = _("My turn.")
        else:
            user = await player.get_user(state.bot, state.key.chat_id)
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
            state: FSMContext,
            user_ids: list[int],
            settings: UnoSettings,
    ) -> "UnoData":
        await state.set_state(PlayStates.UNO)

        deck = await UnoDeck.setup(state.bot)
        players = await UnoPlayers.setup(state, deck, *user_ids)

        return cls(deck=deck, players=players, settings=settings)

    def restart(self):
        self.players.restart(self.deck)

        self.deck = UnoDeck(self.deck.cards_in)
        self.actions = UnoActions()
        self.timer_amount = 3

    async def clear(self, state: FSMContext):
        await self.players.clear(state, self.deck)
        await state.clear()
