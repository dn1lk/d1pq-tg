from random import choice

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.i18n import gettext as _

from bot.utils import timer
from ... import PlayStates

router = Router(name='play:rnd:chat:process')
router.message.filter(PlayStates.RND)


@router.message(F.text.in_(tuple(map(str, range(1, 11)))))
async def process_handler(message: types.Message, state: FSMContext):
    data: dict[str, str | set[int]] = await state.get_data()
    users_guessed = data.setdefault('users_guessed', set())

    if message.from_user.id in users_guessed:
        answer = (
            _("You have already made your choice."),
            _("Cunning, but you already used your try."),
            _("So let's write it down ... Seen in a scam."),
        )
    elif message.text == data['bot_number']:
        answer = (
            _("Yes! This is my number!"),
            _("Someone is fabulously lucky! I guessed this number."),
            _("WE HAVE A WINNER! This is my number!")
        )

        key = StorageKey(
            bot_id=state.key.bot_id,
            chat_id=state.key.chat_id,
            user_id=state.key.user_id,
            destiny='play',
        )

        del timer.tasks[key]
    else:
        users_guessed.add(message.from_user.id)
        await state.set_data(data)

        answer = (
            _("Nope. This is not my number."),
            _("Do you really think that I will choose THIS number?"),
            _("Next..."),
        )

    await message.reply(choice(answer))


@router.message(F.text.isdigit())
async def mistake_handler(message: types.Message):
    await message.reply(
        choice(
            (
                _("So you won’t guess for sure, choose a emoji from 1 to 10!"),
                _("Somebody can't read. It was clearly written, from 1 to 10!"),
                _("Between 1 and 10, what's so difficult?!"),
            )
        )
    )
