import asyncio
from random import choices, choice

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _, ngettext as ___
from pydantic import BaseModel

from bot.handlers import get_username
from .cards import UnoCard, UnoSpecials, UnoColors, get_cards
from .exceptions import UnoNoCardsException, UnoNoUsersException


class UnoPollKick(BaseModel):
    message_id: int
    user_id: int
    amount: int


class UnoData(BaseModel):
    users: dict[int, list[UnoCard]]
    current_user: types.User | None
    next_user: types.User

    current_card: UnoCard | None
    current_special: UnoSpecials = UnoSpecials()

    polls_kick: dict[str, UnoPollKick] = {}
    uno_users_id: set[int] = set()

    timer_amount: int = 3

    async def user_next(self, bot: Bot, chat_id: int, user_id: int | None = None) -> types.User:
        user_id = user_id or self.next_user.id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) + 1]
        except IndexError:
            user_id = users[0]

        return (await bot.get_chat_member(chat_id, user_id)).user

    async def user_prev(self, bot: Bot, chat_id: int, user_id: int | None = None) -> types.User:
        user_id = user_id or self.current_user.id
        users = tuple(self.users)

        try:
            user_id = users[users.index(user_id) - 1]
        except IndexError:
            user_id = users[-1]

        return (await bot.get_chat_member(chat_id, user_id)).user

    async def user_remove(self, state: FSMContext, user_id: int | None = None):
        user_id = user_id or self.current_user.id

        await self.user_remove_state(state, user_id)
        del self.users[user_id]

        if len(self.users) == 1:
            raise UnoNoUsersException("Only one user remained in UNO game")

    async def user_remove_state(self, state: FSMContext, user_id: int | None = None):
        user_id = user_id or self.current_user.id
        key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=user_id,
            user_id=user_id,
            destiny=state.key.destiny
        )

        await state.storage.set_state(state.bot, key)
        await state.storage.update_data(state.bot, key, {'uno_chat_id': None})

    async def user_card_add(self, bot: Bot, user: types.User | None = None, amount: int | None = 1) -> str:
        user = user or self.next_user
        self.users[user.id].extend(choices(await get_cards(bot), k=amount))

        for task in asyncio.all_tasks():
            if task is not asyncio.current_task() and task.get_name() == str(bot) + ':' + str(user.id) + ':' + 'uno':
                task.cancel()
                break

        if user.id in self.uno_users_id:
            self.uno_users_id.remove(user.id)

        if user.id == bot.id:
            return ___(
                "I take {amount} card =(.",
                "I take {amount} cards =(.",
                amount,
            ).format(amount=amount)
        else:
            return ___(
                "{user} receives {amount} card.",
                "{user} receives {amount} cards.",
                amount,
            ).format(
                user=get_username(user),
                amount=amount
            )

    async def current_card_update(self, card: UnoCard):
        self.current_card = card
        self.users[self.current_user.id].remove(card)

        if not self.users[self.current_user.id]:
            raise UnoNoCardsException("The user has run out of cards in UNO game")

    def card_filter(
            self,
            user: types.User,
            sticker: types.Sticker | UnoCard
    ) -> tuple:
        accept, decline = None, None

        if isinstance(sticker, types.Sticker):
            for user_card in self.users[user.id]:
                if user_card.id == sticker.file_unique_id:
                    card = user_card
                    break
            else:
                return sticker, accept, _("What a joke, this card is not from your deck.")
        else:
            card = sticker

        if user.id == self.next_user.id:
            if not self.current_card:
                accept = _("The first move has been made.")
            elif card.color is UnoColors.black:
                accept = _("Black card!")
            elif card.color is self.current_card.color:
                accept = _("So...")

                if self.current_special.color:
                    color = choice(
                        [color for color in UnoColors.names() if color is not self.current_card.color]
                    ).value
                    accept = _("Eh, I should have taken {color[0]} {color[1]} color.").format(color=color)
            elif card.emoji == self.current_card.emoji:
                accept = _("Color change!")
            else:
                decline = choice(
                    (
                        _("Attempt not counted, get a card! =)."),
                        _("Just. Skip. Move."),
                    )
                )
        elif card.emoji == self.current_card.emoji:
            if self.current_user and user.id == self.current_user.id:
                accept = _("Let's keep throwing cards...")
            elif self.current_special.skip and user.id == self.current_special.skip.id and \
                    (not self.current_special.color or card.color is self.current_card.color):
                accept = _("Ha, we throw over the move.")
            elif card.id == self.current_card.id:
                accept = choice(
                    (
                        _("Player {user} managed to take the turn!"),
                        _("I bet {user} will win this game!"),
                        _("Suddenly, {user}."),
                    )
                ).format(user=get_username(user))
            else:
                decline = choice(
                    (
                        _("Hold your horses, {user}. Now is not your turn."),
                        _("Hey {user}, your card doesn't belong this turn."),
                        _("No. No no no. No. {user}, again, no!")
                    )
                ).format(user=get_username(user))
        elif self.current_special.skip and user.id == self.current_user.id == self.current_special.skip.id:
            if card.color in (self.current_card.color, UnoColors.black):
                accept = _("Ha, you're in luck!")
            else:
                decline = _("Good try.")
        else:
            decline = choice(
                (
                    _("Someone explain to this player how to play."),
                    _("Can I just give you a map and we'll pretend like nothing happened?"),
                    _("I'm betting on your defeat."),
                )
            )

        return card, accept, decline

    async def card_special(self, bot: Bot, chat: types.Chat) -> str:
        def reverse():
            self.users = reversed(self.users)
            return choice(
                (
                    _("And vice versa!"),
                    _("A bit of a mess..."),
                )
            ) + "\n" + _("{user} changes the queue.")

        def color():
            self.current_special.color = self.current_card.color
            return choice(
                (
                    _("Finally, we will change the color.\nWhat will {user} choose?"),
                    _("New color, new light.\nby {user}."),
                )
            )

        async def skip():
            self.next_user = self.current_special.skip = await self.user_next(bot, chat.id)
            return choice(
                (
                    _("{user} loses a turn?"),
                    _("{user} risks missing a turn."),
                )
            )

        def draw():
            self.current_special.draw += self.current_card.special.draw
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

        answer = None

        if self.current_card.special.reverse:
            answer = reverse()
        else:
            if self.current_card.special.color:
                answer = color()

            if self.current_card.special.skip:
                answer = await skip()

            if self.current_card.special.draw:
                answer = draw()

        if answer:
            return answer.format(user=get_username(self.current_special.skip or self.current_user))
