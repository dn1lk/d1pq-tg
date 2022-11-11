from random import choice

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from bot.utils.timer import timer
from . import DRAW_CARD
from .misc import UnoData, UnoColors, keyboards as k
from .. import Games

router = Router(name='game:uno:user')
router.message.filter(Games.UNO)


@router.message(F.sticker.set_name == 'uno_by_bp1lh_bot')
class TurnHandler(MessageHandler):
    @property
    def state(self):
        return self.data['state']

    async def handle(self):
        data_uno = await UnoData.get_data(self.state)

        card = data_uno.get_card(self.from_user.id, self.event.sticker)
        accept, decline = data_uno.filter_card(self.from_user.id, card)

        if accept:
            task_name = timer.get_name(self.state, 'game')
            await timer.cancel(task_name)

            data_uno.current_card = card
            data_uno.timer_amount = 3
            data_uno.update_turn(self.from_user.id)

            self.event = await self.proceed_turn(data_uno, accept)

            if self.event:
                from .misc import timeout_proceed, timeout_finally
                timer.create(
                    task_name,
                    coro=timeout_proceed(self.event, self.state),
                    coro_done=timeout_finally(self.event, self.state),
                )

        elif decline:
            data_uno.pick_card(self.from_user)
            await data_uno.set_data(self.state)

            await self.event.reply(decline.format(user=get_username(self.from_user)))

    async def proceed_turn(self, data_uno: UnoData, answer: str):
        if data_uno.current_card.color is UnoColors.BLACK:
            await data_uno.set_data(self.state)

            answer_color = choice(
                (
                    _("Finally, we will change the color.\nWhat will {user} choose?"),
                    _("New color, new light.\nby {user}."),
                )
            )

            return await self.event.answer(
                answer_color.format(user=get_username(self.from_user)),
                reply_markup=k.choice_color(),
            )

        answer = data_uno.update_state() or answer

        if data_uno.current_state.seven:
            await data_uno.set_data(self.state)

            answer_seven = _(
                "{user}, with whom will you exchange cards?\n"
                "Mention (@) this player in your next message."
            )

            return await self.event.answer(
                answer_seven.format(user=get_username(self.from_user)),
            )

        from .misc.process import proceed_turn
        await proceed_turn(self.event, self.state, data_uno, answer)


@router.message(F.text == DRAW_CARD)
async def pass_handler(message: types.Message, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    if message.from_user.id == data_uno.current_user_id:
        await timer.cancel(timer.get_name(state, 'game'))

        answer = data_uno.play_draw(message.from_user)

        from .misc.process import next_turn
        await next_turn(message, state, data_uno, answer)

    else:
        user = await data_uno.get_user(state)
        await message.reply(
            _(
                "Of course, I don't mind, but now it's {user}'s turn.\n"
                "We'll have to wait =)."
            ).format(user=get_username(user))
        )


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.BLUFF))
async def bluff_handler(query: types.CallbackQuery, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    if query.from_user.id == data_uno.current_user_id:
        await timer.cancel(timer.get_name(state, 'game'))

        answer = await data_uno.play_bluff(state)

        from .misc.process import next_turn
        await next_turn(query.message, state, data_uno, answer)

        await query.answer()

    else:
        user = await data_uno.get_user(state)
        answer = _("Only {user} can verify the legitimacy of using this card.")

        await query.answer(answer.format(user=user.first_name))


@router.message(F.entities.func(lambda entities: entities[0].type in ('mention', 'text_mention')))
class SevenHandler(MessageHandler):
    @property
    def state(self) -> FSMContext:
        return self.data['state']

    async def handle(self):
        data_uno = await UnoData.get_data(self.state)

        if self.from_user.id == data_uno.current_state.seven:
            seven_user = await self.get_seven_user(data_uno)

            if seven_user:
                await timer.cancel(timer.get_name(self.state, 'game'))

                answer = data_uno.play_seven(self.event.from_user, seven_user)

                from .misc.process import next_turn
                await next_turn(self.event, self.state, data_uno, answer)

            else:
                await self.event.answer(_("{user} is not playing with us.").format(
                    user=get_username(self.event.entities[0].user))
                )

    async def get_seven_user(self, data_uno: UnoData):
        if self.event.entities[0].user:
            user = self.event.entities[0].user

            if user in data_uno.users:
                return user

        else:
            for user_id in data_uno.users:
                user = await data_uno.get_user(self.state, user_id)

                if f'@{user.username}' == self.event.text.strip():
                    return user


@router.callback_query(k.UnoKeyboard.filter(F.action.in_(UnoColors)))
async def color_handler(
        query: types.CallbackQuery,
        state: FSMContext,
        callback_data: k.UnoKeyboard,
):
    data_uno = await UnoData.get_data(state)

    if query.from_user.id == data_uno.current_user_id:
        await timer.cancel(timer.get_name(state, 'game'))

        data_uno.current_card.color = callback_data.action

        await query.message.edit_text(
            _("{user} changes the color to {color}!").format(
                user=get_username(query.from_user),
                color=data_uno.current_card.color.word,
            )
        )

        answer = data_uno.update_state()

        from .misc.process import proceed_turn
        await proceed_turn(query.message, state, data_uno, answer or "")

        await query.answer()
    else:
        await query.answer(_("When you'll get a BLACK card, choose this color ;)"))


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.UNO))
async def uno_handler(query: types.CallbackQuery, state: FSMContext):
    data_uno = await UnoData.get_data(state)

    if query.from_user.id in data_uno.users:
        task = await timer.cancel(timer.get_name(state, 'game:uno'))

        if not task:
            return query.answer(_("Next time be faster!"))

        from .misc.process import proceed_uno
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
