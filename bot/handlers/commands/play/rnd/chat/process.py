import secrets

from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.play import PlayStates
from utils import TimerTasks

router = Router(name="rnd:chat:process")
router.message.filter(PlayStates.RND)


@router.message(F.text.in_(tuple(map(str, range(1, 11)))))
@flags.timer(cancelled=False)
async def process_handler(message: types.Message, state: FSMContext, timer: TimerTasks) -> None:
    data = await state.get_data()
    bot_number: str = data["bot_number"]
    users_guessed: set[int] = data.setdefault("users_guessed", set())

    if message.from_user.id in users_guessed:
        texts = (
            _("You have already made your choice."),
            _("Cunning, but you already used your try."),
            _("So let's write it down ... Seen in a scam."),
        )
    elif message.text == bot_number:
        del timer[state.key]

        texts = (
            _("Yes! This is my number!"),
            _("Someone is fabulously lucky! I guessed this number."),
            _("WE HAVE A WINNER! This is my number!"),
        )
    else:
        users_guessed.add(message.from_user.id)
        await state.set_data(data)

        texts = (
            _("Nope. This is not my number."),
            _("Do you really think that I will choose THIS number?"),
            _("Next..."),
        )

    content = formatting.Text(secrets.choice(texts))
    await message.reply(**content.as_kwargs())


@router.message(F.text.isdigit())
async def mistake_handler(message: types.Message) -> None:
    content = formatting.Text(
        secrets.choice(
            (
                _("So you won’t guess for sure, choose a emoji from 1 to 10!"),
                _("Somebody can't read. It was clearly written, from 1 to 10!"),
                _("Between 1 and 10, what's so difficult?!"),
            ),
        ),
    )

    await message.reply(**content.as_kwargs())
