from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from .data import UnoData
from .exceptions import UnoNoUsersException
from .process import finish

router = Router(name='game:uno:poll')


async def poll_kick_filter(poll_answer: types.PollAnswer, state: FSMContext):
    data_uno: UnoData = UnoData(**(await state.get_data())['uno'])

    if poll_answer.poll_id in data_uno.polls_kick and poll_answer.option_ids == [0]:
        return {"data_uno": data_uno}


@router.poll_answer(poll_kick_filter)
async def poll_kick_handler(poll_answer: types.PollAnswer, bot: Bot, state: FSMContext, data_uno: UnoData):
    data_uno.polls_kick[poll_answer.poll_id].amount += 1

    if data_uno.polls_kick[poll_answer.poll_id].amount >= (len(data_uno.users) - 1) / 2:
        await bot.delete_message(state.key.chat_id, data_uno.polls_kick[poll_answer.poll_id].message_id)
        user = (await bot.get_chat_member(state.key.chat_id, data_uno.polls_kick[poll_answer.poll_id].user_id)).user
        message = await bot.send_message(
            state.key.chat_id,
            _("{user} is kicked from the game.").format(user=get_username(user)),
        )

        try:
            await data_uno.remove_user(state, data_uno.polls_kick.pop(poll_answer.poll_id).user_id)
            await state.update_data(uno=data_uno.dict())
        except UnoNoUsersException:
            await finish(message, data_uno, state)
