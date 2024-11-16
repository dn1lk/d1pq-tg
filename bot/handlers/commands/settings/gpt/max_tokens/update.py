from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters
from handlers.commands import CommandTypes
from handlers.commands.misc.types import PREFIX
from handlers.commands.settings.gpt import GPTSettingsStates
from utils import TimerTasks, database
from utils.database.types import Uint16

MAX_TOKENS = 2000

router = Router(name="gpt:max_tokens:update")
router.message.filter(GPTSettingsStates.MAX_TOKENS, filters.IsAdmin(is_admin=True))


@router.message(F.text.isdigit() & F.text.func(lambda text: 0 < int(text) <= MAX_TOKENS))
@flags.database("gpt_settings")
async def accept_handler(
    message: types.Message,
    state: FSMContext,
    timer: TimerTasks,
    gpt_settings: database.GPTSettings,
) -> None:
    assert message.text is not None, "wrong text"

    gpt_settings.max_tokens = Uint16(message.text)

    del timer[state.key]
    await gpt_settings.save()
    await state.clear()

    content = formatting.Text(
        formatting.Bold(_("Max tokens has been successfully updated.")),
        "\n",
        _("Current max tokens"),
        ": ",
        formatting.Bold(f"{gpt_settings.max_tokens}"),
        ".",
    )

    await message.answer(**content.as_kwargs())


@router.message()
@flags.database("gpt_settings")
async def decline_handler(
    message: types.Message,
    state: FSMContext,
    timer: TimerTasks,
) -> None:
    data = await state.get_data()
    tries = data.get("tries", 1)

    if tries > 1:
        await state.clear()
        del timer[state.key]

        _command = f"{PREFIX}{CommandTypes.SETTINGS[0]}"
        content = formatting.Text(
            formatting.Bold(_("Something is not working for you.")),
            "\n",
            _("{command} - if you decide to set max tokens again.").format(command=_command),
        )
    else:
        await state.update_data(tries=tries + 1)
        content = formatting.Text(_("Wrong number - I accept only from 0 to 2000."))

    await message.answer(**content.as_kwargs())
