import asyncio
import secrets

from aiogram import F, Router, flags
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.utils import formatting
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.play import PlayActions, PlayStates
from utils import TimerTasks, database

router = Router(name="rnd:chat:start")
router.message.filter(filters.Command(*CommandTypes.PLAY, magic=F.args.in_(PlayActions.RND)))


@router.message()
@flags.timer
class StartHandler(MessageHandler):
    @property
    def state(self) -> FSMContext:
        return self.data["state"]

    @property
    def timer(self) -> TimerTasks:
        return self.data["timer"]

    @property
    def gen_settings(self) -> database.GenSettings:
        return self.data["gen_settings"]

    async def handle(self) -> None:
        if self.from_user:
            _user = formatting.TextMention(self.from_user.first_name, user=self.from_user)
        else:
            _user = _("someone")

        content = formatting.Text(
            _("Hmm"),
            ", ",
            _user,
            " ",
            _(
                "is trying own luck! Well, EVERYONE, EVERYONE, EVERYONE!\n"
                "I guessed a number from 1 to 10.\n"
                "\n"
                "Guess what?",
            ),
        )

        self.event = await self.event.answer(**content.as_kwargs())

        async with ChatActionSender.typing(chat_id=self.chat.id, bot=self.bot):
            await asyncio.sleep(2)

            await self.state.set_state(PlayStates.RND)

            data_rnd = {"bot_number": str(secrets.randbelow(9) + 1)}
            await self.state.set_data(data_rnd)

            content = formatting.Text(_("LET THE BATTLE BEGIN!"))
            self.event = await self.event.answer(**content.as_kwargs())

        self.timer[self.state.key] = self.task(data_rnd)

    async def task(self, data_rnd: dict[str, str]) -> None:
        try:
            await self.wait(data_rnd)
        finally:
            await self.state.clear()

    async def wait(self, data_rnd: dict[str, str]) -> None:
        async def get_stickers():
            for sticker_set_name in (database.DEFAULT_STICKER_SET, *(self.gen_settings.stickers or [])):
                sticker_set = await self.bot.get_sticker_set(sticker_set_name)

                for sticker in sticker_set.stickers:
                    if sticker.emoji in ("⏳", "🙈"):
                        yield sticker

        async with ChatActionSender.choose_sticker(chat_id=self.chat.id, bot=self.bot, interval=10):
            for i in (10, 20, 30):
                await asyncio.sleep(i)
                data_rnd_new = await self.state.get_data()

                if data_rnd_new == data_rnd:
                    if "users_guessed" not in data_rnd_new:
                        return await self.skip()

                    break

                data_rnd = data_rnd_new

            stickers = [sticker async for sticker in get_stickers()]
            await self.bot.send_sticker(self.chat.id, secrets.choice(stickers).file_id)

            await self.finish(data_rnd)

        return None

    async def skip(self) -> None:
        content = formatting.Text(_("Nobody tries to guess!\nI finish the game."))
        await self.event.reply(**content.as_kwargs())

    async def finish(self, data_rnd: dict[str, str]) -> None:
        content = formatting.Text(
            _("Nobody guessed right. 😢\nMy number was"),
            " ",
            formatting.Bold(data_rnd["bot_number"]),
            ".",
        )

        await self.event.reply(**content.as_kwargs())
