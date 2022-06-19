import asyncio
from random import choices, choice

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoSpecials, UnoColors, get_cards
from .exceptions import UnoNoCardsException, UnoNoUsersException, UnoOneCardException


class UnoPollKick(BaseModel):
    message_id: int
    user_id: int
    amount: int


class UnoData(BaseModel):
    users: dict[int, list[UnoCard]]
    current_user_id: int = None
    next_user_id: int

    current_card: UnoCard | None
    current_special: UnoSpecials = UnoSpecials()

    polls_kick: dict[str, UnoPollKick] = {}
    uno_users_id: list[int] = []

    timer_amount: int = 3

    async def get_user(self, bot: Bot, chat_id: int, user_id: int = None) -> types.User:
        user_id = user_id or self.next_user_id
        member = await bot.get_chat_member(chat_id, user_id)
        if member.is_member or user_id in (chat_id, bot.id):
            return member.user
        else:
            raise UnoNoCardsException("User leave from the chat")

    def user_next(self, user_id: int = None) -> int:
        user_id = user_id or self.next_user_id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) + 1]
        except IndexError:
            user_id = users[0]

        return user_id

    def user_prev(self, user_id: int = None) -> int:
        user_id = user_id or self.current_user_id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) - 1]
        except IndexError:
            user_id = users[-1]

        return user_id

    def card_filter(self, user_id: int, sticker: types.Sticker | UnoCard) -> tuple:
        accept, decline = None, None

        if isinstance(sticker, types.Sticker):
            for user_card in self.users[user_id]:
                if user_card.id == sticker.file_unique_id:
                    card = user_card
                    break
            else:
                return sticker, accept, _("What a joke, this card is not from your deck, {user}.")
        else:
            card = sticker

        if user_id == self.next_user_id:
            if not self.current_card:
                accept = _("{user} makes the first move.")
            elif card.color is UnoColors.black:
                accept = _("Black card by {user}!")
            elif card.color is self.current_card.color:
                accept = _("So... {user}.")

                if self.current_special.color:
                    self.current_special.color = False

                    color = choice(list(UnoColors.names(exclude={UnoColors.black, self.current_card.color})))
                    accept = _("Eh, {user}.") + _("You could choose {emoji} {color}!").format(
                        emoji=color.value,
                        color=color.get_color(),
                    )
            elif card.emoji == self.current_card.emoji:
                accept = _("{user} changes color!")
            else:
                decline = choice(
                    (
                        _("{user}, attempt not counted, get a card! =)."),
                        _("{user}... Just. Skip. Move."),
                        _("Someday {user} will be able to make the right move.")
                    )
                )
        elif card.emoji == self.current_card.emoji:
            if user_id == self.current_user_id:
                accept = _("{user} keeps throwing cards...")
            elif user_id == self.current_special.skip and \
                    (not self.current_special.color or card.color is self.current_card.color):
                accept = choice(
                    (
                        _("{user} is unskippable!"),
                        _("{user}, you can't be skipped!"),
                        _("Skips are not for you, {user} =).")
                    )
                )
            elif card.id == self.current_card.id:
                accept = choice(
                    (
                        _("We've been interrupted by {user}!"),
                        _("I bet {user} will win this game!"),
                        _("Suddenly, {user}."),
                    )
                )
            else:
                decline = choice(
                    (
                        _("Hold your horses, {user}. Now is not your turn."),
                        _("Hey, {user}. Your card doesn't belong this turn."),
                        _("No. No no no. No. Again, {user}, NO!")
                    )
                )
        elif user_id == self.current_user_id == self.current_special.skip:
            if card.color in (self.current_card.color, UnoColors.black):
                accept = _("Ha, and {user} is lucky!")
            else:
                decline = _("Good try, {user}.")
        else:
            decline = choice(
                (
                    _("Someone explain to {user} how to play."),
                    _("Can I just give {user} a map and we'll pretend like nothing happened?"),
                    _("I'm betting on {user}'s defeat."),
                )
            )

        return card, accept, decline

    async def add_card(
            self,
            bot: Bot,
            chat_id: int,
            user_id: int,
            amount: int = 1
    ) -> str:
        self.users[user_id].extend(choices(await get_cards(bot), k=amount))

        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and task.get_name().endswith(str(user_id) + ':' + 'uno'):
                task.cancel()
                break

        if user_id in self.uno_users_id:
            self.uno_users_id.remove(user_id)

        if user_id == bot.id:
            answer = _("I take")
        else:
            answer = _("{user} receives").format(user=get_username(await self.get_user(bot, chat_id, user_id)))

        return answer + " " + ___("{amount} card.", "{amount} cards.", amount).format(amount=amount)

    def update_current_card(self, card: UnoCard):
        self.current_card = card
        self.users[self.current_user_id].remove(card)

        if len(self.users[self.current_user_id]) == 1:
            raise UnoOneCardException("The user has one card in UNO game")
        elif not self.users[self.current_user_id]:
            raise UnoNoCardsException("The user has run out of cards in UNO game")

    def special_reverse(self):
        self.users = dict(reversed(self.users.items()))
        self.current_card.special.reverse = False
        return choice(
            (
                _("And vice versa!"),
                _("A bit of a mess..."),
            )
        ) + "\n" + _("{user} changes the queue.")

    def special_color(self):
        self.current_special.color = self.current_card.special.color
        self.current_card.special.color = False
        return choice(
            (
                _("Finally, we will change the color.\nWhat will {user} choose?"),
                _("New color, new light.\nby {user}."),
            )
        )

    def special_skip(self):
        self.next_user_id = self.current_special.skip = self.user_next()
        self.current_card.special.skip = 0
        return choice(
            (
                _("{user} loses a turn?"),
                _("{user} risks missing a turn."),
            )
        )

    def special_draw(self):
        self.current_special.draw += self.current_card.special.draw
        self.current_card.special.draw = 0
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
            self.current_special.draw,
        ).format(amount=self.current_special.draw)

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

        user_id = user_id or self.current_user_id

        await remove_state()
        del self.users[user_id]

        if len(self.users) == 1:
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def end(self, state: FSMContext) -> str:
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and task.get_name().startswith('uno'):
                task.cancel()

        for poll in self.polls_kick.values():
            await state.bot.delete_message(state.key.chat_id, poll.message_id)

        self.next_user_id = tuple(self.users)[0]

        await self.remove_user(state, self.next_user_id)
        await state.clear()

        return _("<b>Game over.</b>\n\n{user} is the last player.")
