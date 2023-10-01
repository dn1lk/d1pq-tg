from random import choice

from aiogram import Bot, Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.utils.i18n import gettext as _

from core.utils import TimerTasks
from handlers.commands.play import PlayStates
from . import DRAW_CARD
from .misc import keyboards
from .misc.actions import proceed_turn, next_turn, proceed_uno
from .misc.actions.turn import update_timer
from .misc.data import UnoData
from .misc.data.deck import UnoCard
from .misc.data.deck.base import STICKER_SET_NAME

router = Router(name='uno:user')
router.message.filter(PlayStates.UNO)
router.callback_query.filter(PlayStates.UNO)


@router.message(
    F.sticker.set_name == STICKER_SET_NAME,
    UnoData.filter('turn')
)
@flags.timer
async def turn_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        card: UnoCard,
        answer: str
):
    data_uno = await UnoData.get_data(state)
    await proceed_turn(message, bot, state, timer, data_uno, card, answer)


@router.message(
    F.text == DRAW_CARD,
    UnoData.filter('pass')
)
@flags.timer
async def pass_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
):
    data_uno = await UnoData.get_data(state)
    answer = data_uno.do_pass(message.from_user)

    await next_turn(message, bot, state, timer, data_uno, answer)


@router.callback_query(
    keyboards.UnoData.filter(F.action == keyboards.UnoActions.BLUFF),
    UnoData.filter('bluff')
)
@flags.timer
async def bluff_handler(
        query: types.CallbackQuery,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
):
    data_uno = await UnoData.get_data(state)

    answer = await data_uno.do_bluff(bot, state.key.chat_id)
    answer_next = await data_uno.do_next(bot, state)

    message = await query.message.edit_text(
        f'{answer}\n{answer_next}',
        reply_markup=keyboards.show_cards(bluffed=False)
    )

    await update_timer(message, bot, state, timer, data_uno)
    await query.answer()


@router.message(F.entities.func(lambda entities: entities[0].type in ('mention', 'text_mention')))
@flags.timer(cancelled=False, locked=False)
class SevenHandler(MessageHandler):
    @property
    def bot(self) -> Bot:
        return self.data["bot"]

    @property
    def state(self) -> FSMContext:
        return self.data['state']

    @property
    def timer(self) -> TimerTasks:
        return self.data['timer']

    async def filter(self):
        data_uno = await UnoData.get_data(self.state)
        current_id = data_uno.players.current_id

        if self.from_user.id == current_id:
            chosen_user = await self._get_seven_user(data_uno)

            if chosen_user:
                del self.timer[self.state.key]
                return chosen_user

            else:
                answer = _("{user} is not playing with us.").format(user=chosen_user.mention_html())

        else:
            user = await data_uno.players.get_user(self.bot, self.state.key.chat_id, current_id)
            answer = _("Only {user} can choose with whom to exchange cards.").format(user=html.quote(user.first_name))

        await self.event.answer(answer)

    async def handle(self):
        chosen_user = await self.filter()

        if chosen_user:
            async with self.timer.lock(self.state.key):
                await self.proceed(chosen_user)

    async def _get_seven_user(self, data_uno: UnoData) -> types.User | None:
        if self.event.entities[0].user:
            user = self.event.entities[0].user

            if user.id in data_uno.players.playing:
                return user

        else:
            for player_id in data_uno.players.playing:
                user = await data_uno.players.get_user(self.bot, self.state.key.chat_id, player_id)

                if f'@{user.username}' in self.event.text:
                    return user

    async def proceed(self, chosen_user: types.User):
        data_uno = await UnoData.get_data(self.state)

        answer = data_uno.do_seven(chosen_user.id)
        await next_turn(self.event, self.bot, self.state, self.timer, data_uno, answer)


@router.callback_query(
    keyboards.UnoData.filter(F.action == keyboards.UnoActions.COLOR),
    UnoData.filter('color')
)
@flags.timer
async def color_handler(
        query: types.CallbackQuery,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        callback_data: keyboards.UnoData,
):
    data_uno = await UnoData.get_data(state)

    # Update card color
    color = callback_data.value
    answer_color = data_uno.do_color(color)

    message = await query.message.edit_text(
        _("{user} changes the color to {color}!").format(
            user=query.from_user.mention_html(),
            color=color,
        )
    )

    await next_turn(message, bot, state, timer, data_uno, answer_color or "")
    await query.answer()


@router.callback_query(
    keyboards.UnoData.filter(F.action == keyboards.UnoActions.UNO),
    UnoData.filter('uno')
)
@flags.timer(cancelled=False)
async def uno_handler(query: types.CallbackQuery, bot: Bot, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    if not query.message.entities or query.from_user.id != query.message.entities[-1].user.id:
        await proceed_uno(query.message, bot, state, data_uno, query.from_user)

    answer = (
        _("Good job!"),
        _("And you don't want to lose. 😎"),
        _("On reaction. 😎"),
        _("Yep!"),
        _("Like a pro.")
    )

    await query.answer(choice(answer))
