from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions, PlayStates
from handlers.commands.play.rnd.misc.timer import task
from utils import TimerTasks

router = Router(name="start")
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RND)))


@router.message()
@flags.timer
async def start_handler(message: types.Message, state: FSMContext, timer: TimerTasks) -> None:
    await state.set_state(PlayStates.RND)

    content = formatting.Text(_("Hmm, you're trying own luck!\nI guessed a number from 1 to 10.\n\nGuess what?"))
    message = await message.answer(**content.as_kwargs())

    timer[state.key] = task(message, state)
