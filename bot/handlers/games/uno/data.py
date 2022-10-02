import asyncio
from random import choices, choice

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoColors, UnoEmoji, get_cards
from .exceptions import UnoNoCardsException, UnoNoUsersException, UnoOneCardException


class UnoUser(BaseModel):
    cards: list[UnoCard]
    played_cards: int = 0


class UnoPollKick(BaseModel):
    message_id: int
    poll_id: int
    amount: int = 0


class UnoData(BaseModel):
    users: dict[int, UnoUser]
    current_user_id: int

    current_card: UnoCard | None = None
    current_draw: int = 0
    current_skip: int | bool = False

    bot_speed: float

    winners: dict = {}

    polls_kick: dict[int, UnoPollKick] = {}
    timer_amount: int = 3

    @property
    def prev_user_id(self) -> int:
        users = tuple(self.users)

        try:
            user_id = users[users.index(self.current_user_id) - 1]
        except IndexError:
            user_id = users[-1]

        return user_id

    @property
    def next_user_id(self) -> int:
        users = tuple(self.users)

        try:
            user_id = users[users.index(self.current_user_id) + 1]
        except IndexError:
            user_id = users[0]

        return user_id

    def check_sticker(self, user_id, sticker: types.Sticker) -> UnoCard | None:
        for user_card in self.users[user_id].cards:
            if user_card.id == sticker.file_unique_id:
                return user_card

    def filter_card(self, user_id: int, card: UnoCard | None) -> tuple[str | bool, str | bool]:
        accept, decline = False, False

        if not card:
            return accept, _("What a joke, this card is not from your deck, {user}.")

        if user_id == self.current_user_id:
            if not self.current_card:
                accept = _("{user} makes the first move.")
            elif card.color is UnoColors.black:
                accept = _("Black card by {user}!")
            elif card.color is self.current_card.color:
                accept = choice(
                    (
                        _("So... {user}."),
                        _("Wow, you got {emoji} {color}!").format(
                            emoji=card.color.value,
                            color=card.color.name
                        ),
                    )
                )
            elif card.emoji == self.current_card.emoji:
                accept = _("{user} changes color!")
            else:
                decline = choice(
                    (
                        _("{user}, attempt not counted, get a card! =)."),
                        _("Just. Skip. Turn."),
                        _("Someday {user} will be able to make the right move.")
                    )
                )

        elif user_id == self.prev_user_id:
            if self.current_card.emoji in (UnoEmoji.skip, UnoEmoji.draw):
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} is unskippable!"),
                            _("{user}, you can't be skipped!"),
                            _("Skips are not for you =).")
                        )
                    )
                else:
                    decline = _("{user}, your turn is skipped =(.")
            else:
                if card.emoji == self.current_card.emoji:
                    accept = choice(
                        (
                            _("{user} keeps throwing cards..."),
                            _("{user}, will anyone stop you?"),
                        )
                    )
                else:
                    decline = _("{user}, you have already made your turn.")

        elif card.id == self.current_card.id:
            accept = choice(
                (
                    _("We've been interrupted!"),
                    _("I bet {user} will win this game!"),
                    _("Suddenly, {user}."),
                )
            )

        else:
            decline = choice(
                (
                    _("Hold your horses, {user}. Now is not your turn."),
                    _("Hey, {user}. Your card doesn't belong this turn."),
                    _("No. No no no. No. Again, NO!"),
                    _("Someone explain to {user} how to play."),
                    _("Can I just give {user} a card and we'll pretend like nothing happened?"),
                    _("I'm betting on {user}'s defeat."),
                )
            )

        return accept, decline

    async def add_card(self, bot: Bot, user: types.User, amount: int = 1) -> str:
        self.users[user.id].cards.extend(choices(await get_cards(bot), k=amount))

        if user.id == bot.id:
            answer = _("I take")
        else:
            answer = _("{user} receives").format(user=get_username(user))

        return answer + " " + ___("{amount} card.", "{amount} cards.", amount).format(amount=amount)

    def update_current_user_id(self, user_id):
        self.current_user_id = user_id
        self.users[self.current_user_id].cards.remove(self.current_card)
        self.users[self.current_user_id].played_cards += 1

        if len(self.users[self.current_user_id].cards) == 1:
            raise UnoOneCardException("The user has one card in UNO game")
        elif not self.users[self.current_user_id].cards:
            self.winners[self.current_user_id] = self.users[self.current_user_id].played_cards
            raise UnoNoCardsException("The user has run out of cards in UNO game")

    async def update_current_special(self):
        if self.current_card.emoji == UnoEmoji.reverse:
            return self.special_reverse()

        elif self.current_card.emoji == UnoEmoji.draw:
            return self.special_draw()

        elif self.current_card.emoji == UnoEmoji.skip:
            return self.special_skip()

    async def apply_current_special(self, state: FSMContext):
        if self.current_draw:
            user = (await state.bot.get_chat_member(state.key.chat_id, self.prev_user_id)).user
            answer = await self.add_card(state.bot, user, self.current_draw)
            self.current_draw = 0

            return answer

        self.current_skip = False

    def special_reverse(self) -> str:
        if len(self.users) > 2:
            self.users = dict(reversed(self.users.items()))
            return choice(
                (
                    _("And vice versa!"),
                    _("A bit of a mess..."),
                )
            ) + "\n" + _("{user} changes the queue.")

        return self.special_skip()

    def special_skip(self) -> str:
        self.current_user_id = self.current_skip = self.next_user_id
        return choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
            )
        )

    def special_draw(self) -> str:
        self.current_user_id = self.next_user_id
        self.current_draw += 2

        return choice(
            (
                _("How cruel!"),
                _("What a surprise."),
            )
        ) + "\n" + choice(
            (
                _("{user} risks getting"),
                _("{user} can get"),
            )
        ) + " " + ___(
            "<b>{amount}</b> card!",
            "<b>{amount}</b> cards!",
            self.current_draw,
        ).format(amount=self.current_draw)

    def special_color(self) -> str:
        if self.current_card.emoji == UnoEmoji.draw:
            self.current_draw += 2

        return choice(
            (
                _("Finally, we will change the color.\nWhat will {user} choose?"),
                _("New color, new light.\nby {user}."),
            )
        )

    async def remove_user(self, state: FSMContext, user_id: int = None):
        async def remove_state():
            key = StorageKey(
                bot_id=state.key.bot_id,
                chat_id=user_id,
                user_id=user_id,
                destiny=state.key.destiny,
            )

            await state.storage.set_state(state.bot, key)
            await state.storage.set_data(state.bot, key, {})

        if not user_id:
            user_id = self.current_user_id
            self.current_user_id = self.prev_user_id

        await remove_state()
        del self.users[user_id]

        if len(self.users) == 1:
            user_id = tuple(self.users)[0]
            self.winners[user_id] = self.users[user_id].played_cards
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def finish(self, state: FSMContext) -> str:
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and task.get_name().startswith('uno'):
                task.cancel()

        for poll in self.polls_kick.values():
            await state.bot.delete_message(state.key.chat_id, poll.message_id)

        try:
            for user_id in tuple(self.users):
                await self.remove_user(state, user_id)
        except UnoNoUsersException:
            await self.remove_user(state)

        await state.clear()

        return _("<b>Game over.</b>\n")
