import asyncio
from random import choice

from aiogram import Router, F, flags
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.handlers import MessageHandler
from aiogram.utils.i18n import gettext as _

from bot import filters
from bot.handlers.commands import CommandTypes
from bot.handlers.commands.play import PlayActions, PlayStates, CLOSE
from bot.utils import timer

router = Router(name='start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RND)))


@router.message()
@flags.timer('play')
class StartHandler(MessageHandler):
    @property
    def state(self) -> FSMContext:
        return self.data['state']

    @property
    def timer_key(self) -> StorageKey:
        return self.data['timer_key']

    async def handle(self):
        await self.state.set_state(PlayStates.RND)

        answer = _(
            "Hmm, you're trying your luck!\n"
            "I guessed a number from one to ten.\n"
            "\n"
            "Guess what number?"
        )

        self.event = await self.event.answer(answer)

        timer.tasks[self.timer_key] = self.task()

    async def task(self):
        try:
            await asyncio.sleep(choice(range(40, 120)))
            await self.event.reply(str(choice(CLOSE)))
        finally:
            await self.state.clear()
