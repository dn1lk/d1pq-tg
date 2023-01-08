import asyncio
from random import choice

from aiogram import Router, types, F, html, flags
from aiogram.fsm.context import FSMContext
from aiogram.handlers import MessageHandler
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from bot.utils.timer import timer
from .. import Games, close_timeout
from ... import get_username
from ...settings.commands import CustomCommandFilter

router = Router(name='game:rnd:start')
router.message.filter(CustomCommandFilter(commands=['play', 'поиграем'], magic=F.args.in_(('rnd', 'рнд'))))


@router.message(F.chat.type == 'private')
@flags.timer('game')
async def private_handler(message: types.Message, state: FSMContext):
    await state.set_state(Games.RND)
    message = await message.answer(
        _(
            "Hmm, you are trying your luck... Well, ender any number between 1 and 10 and I'll choose "
            "my own and we find out if our thoughts are the same ;)."
        )
    )

    return timer.dict(close_timeout(message, state))


@router.message()
@flags.timer(('game', 0))
class ChatHandler(MessageHandler):
    @property
    def state(self) -> FSMContext:
        return self.data['state']

    @property
    def db(self) -> DataBaseContext:
        return self.data['db']

    async def handle(self):
        answer = _(
            "Mm, {user} is trying his luck... Well, EVERYONE, EVERYONE, EVERYONE, pay attention!\n\n"
            "Enter any number between 1 and 10 and I'll choose "
            "my own in 60 seconds and we'll see which one of you is right."
        )

        self.event = await self.event.answer(answer.format(user=get_username(self.from_user)))

        async with ChatActionSender.typing(chat_id=self.chat.id):
            await asyncio.sleep(2)

            await self.state.set_state(Games.RND)
            await self.state.set_data({})

            self.event = await self.event.answer(_("LET THE BATTLE BEGIN!"))

        return timer.dict(self.wait(), self.finish())

    async def wait(self):
        async def get_stickers():
            for sticker_set in await self.db.get_data('stickers'):
                yield await self.bot.get_sticker_set(sticker_set)

        def filter_sticker(sticker: types.Sticker):
            return sticker.emoji in ('⏳', '🙈')

        async with ChatActionSender.choose_sticker(chat_id=self.chat.id, interval=20):
            await asyncio.sleep(60)

            stickers = sum([stickers.stickers async for stickers in get_stickers()], [])
            await self.bot.send_sticker(self.chat.id, choice(list(filter(filter_sticker, stickers))).file_id)

    async def finish(self):
        user_vars: dict[str, list[int]] = await self.state.get_data() or {}
        await self.state.clear()

        bot_var = str(choice(range(1, 11)))
        answer = _("So, my variant is {bot_var}.\n").format(bot_var=html.bold(bot_var))

        winners = user_vars.get(bot_var)

        if winners:
            async def get_member():
                for user_id in winners:
                    yield await self.bot.get_chat_member(self.chat.id, user_id)

            winners = ', '.join([get_username(winner.user) async for winner in get_member()])
            answer += _('The title of winner goes to: {winners}. Congrats!').format(winners=winners)
        else:
            answer += _("No one guessed right. Heh.")

        await self.event.reply(answer)
