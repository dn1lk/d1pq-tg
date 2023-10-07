import asyncio
from random import choice, randint

from aiogram import Router, F, html, flags
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from core import filters
from core.utils import TimerTasks, database
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions, PlayStates

router = Router(name='rnd:chat:start')
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RND)))


@router.message()
@flags.timer
class StartHandler(MessageHandler):

    @property
    def state(self) -> FSMContext:
        return self.data['state']

    @property
    def timer(self) -> TimerTasks:
        return self.data['timer']

    @property
    def gen_settings(self) -> database.GenSettings:
        return self.data['gen_settings']

    async def handle(self):
        answer = _(
            "Hmm, {user} is trying own luck! Well, EVERYONE, EVERYONE, EVERYONE!\n"
            "I guessed a number from 1 to 10.\n"
            "\n"
            "Guess what?"
        )

        self.event = await self.event.answer(answer.format(user=self.from_user.mention_html()))

        async with ChatActionSender.typing(chat_id=self.chat.id, bot=self.bot):
            await asyncio.sleep(2)

            await self.state.set_state(PlayStates.RND)

            data_rnd = {'bot_number': str(randint(1, 10))}
            await self.state.set_data(data_rnd)

            self.event = await self.event.answer(_("LET THE BATTLE BEGIN!"))

        self.timer[self.state.key] = self.task(data_rnd)

    async def task(self, data_rnd: dict[str, str | set[int]]):
        try:
            await self.wait(data_rnd)
        finally:
            await self.state.clear()

    async def wait(self, data_rnd: dict[str, str | set[int]]):
        async def get_stickers():
            for sticker_set_name in (database.DEFAULT_STICKER_SET, *(self.gen_settings.stickers or [])):
                sticker_set = await self.bot.get_sticker_set(sticker_set_name)

                for sticker in sticker_set.stickers:
                    if sticker.emoji in ('⏳', '🙈'):
                        yield sticker

        async with ChatActionSender.choose_sticker(chat_id=self.chat.id, bot=self.bot, interval=10):
            for i in (10, 20, 30):
                await asyncio.sleep(i)
                data_rnd_new = await self.state.get_data()

                if data_rnd_new == data_rnd:
                    if 'users_guessed' not in data_rnd_new:
                        return await self.skip()

                    break

                data_rnd = data_rnd_new

            stickers = [sticker async for sticker in get_stickers()]
            await self.bot.send_sticker(self.chat.id, choice(stickers).file_id)

            await self.finish(data_rnd)

    async def skip(self):
        answer = _(
            "Nobody tries to guess!\n"
            "I finish the game."
        )

        await self.event.reply(answer)

    async def finish(self, data_rnd: dict[str, str | set[int]]):
        answer = _(
            "Nobody guessed right. 😢\n"
            "My number was {bot_number}."
        ).format(bot_number=html.bold(data_rnd['bot_number']))

        await self.event.reply(answer)
