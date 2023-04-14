from random import choice

from aiogram import Router, F, types, flags, html
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
        state: FSMContext,
        timer: TimerTasks,
        data_uno: UnoData,
        card: UnoCard,
        answer: str
):
    await proceed_turn(message, state, timer, data_uno, card, answer)


@router.message(F.text == DRAW_CARD)
@flags.timer(name='play', cancelled=False)
async def pass_handler(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
):
    data_uno = await UnoData.get_data(state)

    if message.from_user.id == data_uno.players.current_player:
        del timer[state.key]

        answer = await data_uno.do_pass(state)
        await next_turn(message, state, timer, data_uno, answer)

    else:
        user = await data_uno.players.current_player.get_user(state.bot, state.key.chat_id)
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
        state: FSMContext,
        timer: TimerTasks,
):
    data_uno = await UnoData.get_data(state)

    user = query.from_user
    current_player = data_uno.players.current_player

    if user.id == current_player:
        del timer[state.key]

        answer = await data_uno.do_bluff(state)
        await next_turn(query.message, state, timer, data_uno, answer)

        await query.answer()

    else:
        user = await current_player.get_user(state.bot, state.key.chat_id)
        answer = _("Only {user} can verify the legitimacy of using this card.")

        await query.answer(answer.format(user=html.quote(user.first_name)))


@router.message(F.entities.func(lambda entities: entities[0].type in ('mention', 'text_mention')))
@flags.timer(name='play', cancelled=False)
class SevenHandler(MessageHandler):
    @property
    def state(self) -> FSMContext:
        return self.data['state']

    @property
    def timer(self) -> TimerTasks:
        return self.data['timer']

    async def handle(self):
        data_uno = await UnoData.get_data(self.state)
        player = data_uno.players.current_player

        if self.from_user.id == player:
            chosen_user = await self.get_seven_user(data_uno)

            if chosen_user:
                del self.timer[self.state.key]

                answer = data_uno.do_seven(data_uno.players(chosen_user.id))
                await next_turn(self.event, self.state, self.timer, data_uno, answer)

            else:
                answer = _("{user} is not playing with us.").format(user=chosen_user.mention_html())
                await self.event.answer(answer)

        else:
            user = await player.get_user(self.state.bot, self.state.key.chat_id)
            answer = _("Only {user} can choose with whom to exchange cards.")

            await self.event.answer(answer.format(user=html.quote(user.first_name)))

    async def get_seven_user(self, data_uno: UnoData) -> types.User:
        if self.event.entities[0].user:
            user = self.event.entities[0].user

            if data_uno.players(user.id):
                return user

        else:
            for player in data_uno.players:
                user = await player.get_user(self.state, self.state.key.chat_id)

                if f'@{user.username}' == self.event.text.strip():
                    return user


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.COLOR))
@flags.timer(name='play', cancelled=False)
async def color_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        timer: TimerTasks,
        callback_data: keyboards.UnoData,
):
    data_uno = await UnoData.get_data(state)
    user = query.from_user

    if user.id == data_uno.players.current_player:
        # Cancel all current play tasks
        del timer[state.key]

        # Update card color
        color = callback_data.value
        data_uno.deck[-1] = data_uno.deck.last_card.replace(color=color)

        message = await query.message.edit_text(
            _("{user} changes the color to {color}!").format(
                user=user.mention_html(),
                color=color,
            )
        )

        answer = data_uno.update_action()
        await next_turn(message, state, timer, data_uno, answer or "")

        await query.answer()
    else:
        await query.answer(_("When you'll get a BLACK card, choose this color ;)"))


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.UNO))
async def uno_handler(query: types.CallbackQuery, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    if data_uno.players(query.from_user.id):
        timer_uno = TimerTasks('say_uno')
        tasks = set(timer_uno[state.key])

        if not tasks:
            await query.answer(_("Next time be faster!"))
            return

        for task in tasks:
            task.cancel()

        if query.from_user.id != data_uno.players[-1]:
            await proceed_uno(query.message, state, data_uno, query.from_user)

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
