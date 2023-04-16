from random import choice

from aiogram import Bot, Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.utils.i18n import gettext as _

from bot.core.utils import TimerTasks
from . import DRAW_CARD
from .misc import keyboards
from .misc.actions import proceed_turn, next_turn, proceed_uno
from .misc.data import UnoData
from .misc.data.deck import UnoCard
from .. import PlayStates

router = Router(name='play:uno:user')
router.message.filter(PlayStates.UNO)
router.callback_query.filter(PlayStates.UNO)


@router.message(F.sticker.set_name == 'uno_by_d1pq_bot', UnoData.filter())
@flags.timer(name='play')
async def turn_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        card: UnoCard,
        answer: str
):
    await proceed_turn(message, bot, state, timer, data_uno, card, answer)


@router.message(F.text == DRAW_CARD)
@flags.timer(name='play', cancelled=False)
async def pass_handler(
        message: types.Message,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
):
    data_uno = await UnoData.get_data(state)

    user = message.from_user
    current_id = data_uno.players.current_id

    if user.id == current_id:
        del timer[state.key]

        answer = data_uno.do_pass(user)
        await next_turn(message, bot, state, timer, data_uno, answer)

    else:
        user = await data_uno.players.get_user(bot, state.key.chat_id, current_id)
        await message.reply(
            _(
                "Of course, I don't mind, but now it's {user}'s turn.\n"
                "We'll have to wait =)."
            ).format(user=user.mention_html())
        )


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.BLUFF))
@flags.timer(name='play', cancelled=False)
async def bluff_handler(
        query: types.CallbackQuery,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
):
    data_uno = await UnoData.get_data(state)

    user = query.from_user
    current_id = data_uno.players.current_id

    if user.id == current_id:
        del timer[state.key]

        answer = await data_uno.do_bluff(bot, state.key.chat_id)
        await next_turn(query.message, bot, state, timer, data_uno, answer)

        await query.answer()

    else:
        user = await data_uno.players.get_user(state.bot, state.key.chat_id, current_id)
        answer = _("Only {user} can do that.")

        await query.answer(answer.format(user=user.first_name))


@router.message(F.entities.func(lambda entities: entities[0].type in ('mention', 'text_mention')))
@flags.timer(name='play', cancelled=False)
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

    async def handle(self):
        data_uno = await UnoData.get_data(self.state)

        user = self.from_user
        current_id = data_uno.players.current_id

        if user.id == current_id:
            chosen_user = await self.get_seven_user(data_uno)

            if chosen_user:
                del self.timer[self.state.key]

                answer = data_uno.do_seven(chosen_user.id)
                await next_turn(self.event, self.bot, self.state, self.timer, data_uno, answer)

            else:
                answer = _("{user} is not playing with us.").format(user=chosen_user.mention_html())
                await self.event.answer(answer)

        else:
            user = await data_uno.players.get_user(self.bot, self.state.key.chat_id, current_id)
            answer = _("Only {user} can choose with whom to exchange cards.")

            await self.event.answer(answer.format(user=html.quote(user.first_name)))

    async def get_seven_user(self, data_uno: UnoData) -> types.User:
        if self.event.entities[0].user:
            user = self.event.entities[0].user

            if user.id in data_uno.players.playing:
                return user

        else:
            for player_id in data_uno.players.playing:
                user = await data_uno.players.get_user(self.bot, self.state.key.chat_id, player_id)

                if f'@{user.username}' in self.event.text:
                    return user


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.COLOR))
@flags.timer(name='play', cancelled=False)
async def color_handler(
        query: types.CallbackQuery,
        bot: Bot,
        state: FSMContext,
        timer: TimerTasks,
        callback_data: keyboards.UnoData,
):
    data_uno = await UnoData.get_data(state)

    user = query.from_user
    current_id = data_uno.players.current_id

    if user.id == current_id:
        # Cancel all current play tasks
        del timer[state.key]

        # Update card color
        color = callback_data.value
        answer_color = data_uno.do_color(color)

        message = await query.message.edit_text(
            _("{user} changes the color to {color}!").format(
                user=user.mention_html(),
                color=color,
            )
        )

        # Check for DRAW_FOUR card
        await next_turn(message, bot, state, timer, data_uno, answer_color or "")
        await query.answer()
    else:
        await query.answer(_("Nice try."))


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.UNO))
async def uno_handler(query: types.CallbackQuery, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    user = query.from_user

    if user.id in data_uno.players.playing:
        timer_uno = TimerTasks('say_uno')
        tasks = set(timer_uno[state.key])

        if not tasks:
            await query.answer(_("Next time be faster!"))
            return

        for task in tasks:
            task.cancel()

        if not query.message.entities or query.from_user.id != query.message.entities[-1].user.id:
            await proceed_uno(query.message, state, data_uno, user)

        answer = (
            _("Good job!"),
            _("And you don't want to lose =)"),
            _("On reaction =)."),
            _("Yep!"),
            _("Like a pro.")
        )

        await query.answer(choice(answer))

    else:
        await query.answer(_("You are not in the game!"))
