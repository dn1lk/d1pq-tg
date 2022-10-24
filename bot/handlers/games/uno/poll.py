import asyncio

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from .process import UnoData

router = Router(name='game:uno:poll')


async def close_poll_timer(message: types.Message, state: FSMContext, user: types.User):
    try:
        await asyncio.sleep(60)
    except asyncio.CancelledError:
        poll = await state.bot.stop_poll(message.chat.id, message.message_id)
        data_uno: UnoData = UnoData(**(await state.get_data())['uno'])

        if poll.options[0].voter_count > poll.options[1].voter_count and user.id in data_uno.users:
            from .process.core import kick_for_inactivity

            await kick_for_inactivity(message, data_uno, state, user)
    finally:
        await message.delete()


async def poll_kick_filter(poll: types.Poll):
    for task in asyncio.all_tasks():
        if task.get_name() == f'uno:{poll.id}':
            return {'task': task}


@router.poll(poll_kick_filter)
async def poll_kick_handler(poll: types.Poll, data_uno: UnoData, task: asyncio.Task):
    if poll.total_voter_count >= (len(data_uno.users) - 1) / 2:
        task.cancel()
