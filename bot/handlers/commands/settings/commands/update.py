import secrets

from aiogram import F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from handlers.commands import CommandTypes
from handlers.commands.misc.helpers import get_help_content
from handlers.commands.settings import SettingsStates
from utils import TimerTasks, database

router = Router(name="commands:update")
router.message.filter(
    SettingsStates.COMMANDS,
    filters.Command(*(command[0] for command in list(CommandTypes)[:-1]), with_customs=False),
    filters.IsAdmin(is_admin=True),
)


@router.message(filters.MagicData(F.command.args.regexp(r"^\w{1,10}$")))
async def accept_handler(
    message: types.Message,
    state: FSMContext,
    timer: TimerTasks,
    command: filters.CommandObject,
    main_settings: database.models.MainSettings,
) -> None:
    assert command.args is not None, "wrong command args"
    saved_commands = main_settings.commands

    _custom_command = f"{command.prefix}{command.args}"
    if command.args in saved_commands.values():
        content = formatting.Text(
            _("{custom_command} is already recorded. Try another.").format(custom_command=_custom_command),
        )
    elif command.args in sum((enum.value for enum in CommandTypes), ()):
        content = formatting.Text(
            _("{custom_command} is already taken by me. Choose another.").format(custom_command=_custom_command),
        )
    else:
        saved_commands[command.command] = command.args
        del timer[state.key]

        main_settings.commands = saved_commands
        await state.clear()

        _command = f"{command.prefix}{command.command}"
        content = formatting.Text(
            formatting.Bold(_("{custom_command} added successfully!").format(custom_command=_custom_command)),
            "\n\n",
            _("Now in this chat you can write it instead of {command}.").format(command=_command),
        )

    await message.answer(**content.as_kwargs())


@router.message()
@flags.database("gen_settings")
async def decline_handler(
    message: types.Message,
    state: FSMContext,
    timer: TimerTasks,
    command: filters.CommandObject,
    gen_settings: database.models.GenSettings,
) -> None:
    data = await state.get_data()
    tries = data.get("tries", 1)

    if tries > 1:
        await state.clear()
        del timer[state.key]

        _command = f"{command.prefix}{CommandTypes.SETTINGS[0]}"
        content = formatting.Text(
            formatting.Bold(_("Something is not working for you.")),
            "\n",
            _("{command} - if you decide to set your command again.").format(command=_command),
        )
    else:
        await state.update_data(tries=tries + 1)

        content = formatting.Bold(_("Custom command not recognized."))
        message = await message.answer(**content.as_kwargs())

        messages = gen_settings.messages if gen_settings.with_messages else [_("bla bla")]
        content = get_help_content(
            command,
            secrets.choice(helpers.get_split_text(messages)).lower(),
        )

    await message.answer(**content.as_kwargs())
