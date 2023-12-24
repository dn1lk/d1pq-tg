from random import choice

from aiogram import Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from core import filters, helpers
from core.utils import database, TimerTasks
from handlers.commands import CommandTypes
from .. import SettingsStates

router = Router(name='commands:update')
router.message.filter(SettingsStates.COMMANDS,
                      filters.Command(*(command[0] for command in list(CommandTypes)[:-1]), with_customs=False),
                      filters.IsAdmin(is_admin=True))


@router.message(filters.MagicData(F.command.args.regexp(r'^\w{1,10}$')))
async def accept_handler(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        command: filters.CommandObject,
        main_settings: database.MainSettings,
):
    if command.args in main_settings.commands.values():
        answer = _("{prefix}{custom_command} is already recorded. Try another.").format(
            prefix=command.prefix,
            custom_command=command.args,
        )
    elif command.args in sum((enum.value for enum in CommandTypes), ()):
        answer = _("{prefix}{custom_command} is already taken by me. Choose another.").format(
            prefix=command.prefix,
            custom_command=command.args,
        )
    else:
        main_settings.commands[command.command] = command.args

        del timer[state.key]
        await main_settings.save()
        await state.clear()

        answer = _(
            "<b>{prefix}{custom_command} added successfully!</b>\n\n"
            "Now in this chat you can write it instead of {prefix}{command}."
        ).format(
            prefix=command.prefix,
            command=command.command,
            custom_command=command.args,
        )

    await message.answer(answer)


@router.message()
@flags.database('gen_settings')
async def decline_handler(
        message: types.Message,
        state: FSMContext,
        timer: TimerTasks,
        command: filters.CommandObject,
        gen_settings: database.GenSettings,
):
    data = await state.get_data()
    tries = data.get('tries', 1)

    if tries > 1:
        await state.clear()
        del timer[state.key]

        answer = _(
            "<b>Something is not working for you.</b>\n"
            "{command} - if you decide to set your command again."
        ).format(command=f'{command.prefix}{CommandTypes.SETTINGS[0]}')

        await message.answer(answer)
    else:
        await state.update_data(tries=tries + 1)

        from handlers.commands.help import get_answer

        message = await message.answer(html.bold(_("Custom command not recognized.")))
        answer = get_answer(
            command,
            choice(helpers.get_split_text(gen_settings.messages or [_('bla bla')])).lower()
        )

        await message.answer(answer)
