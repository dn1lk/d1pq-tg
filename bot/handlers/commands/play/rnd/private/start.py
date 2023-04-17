import asyncio
from random import choice, randint

from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.core import filters
from bot.core.utils import TimerTasks
from bot.handlers.commands import CommandTypes
from bot.handlers.commands.play import PlayActions, PlayStates, CLOSE

router = Router(name='start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RND)))


async def task(message: types.Message, state: FSMContext):
    try:
        await asyncio.sleep(randint(40, 120))
        await message.reply(str(choice(CLOSE)))
    finally:
        await state.clear()


@router.message()
@flags.timer('play')
async def start_handler(message: types.Message, state: FSMContext, timer: TimerTasks):
    await state.set_state(PlayStates.RND)

    answer = _(
        "Hmm, you're trying own luck!\n"
        "I guessed a number from 1 to 10.\n"
        "\n"
        "Guess what?"
    )

    message = await message.answer(answer)
    timer[state.key] = task(message, state)
