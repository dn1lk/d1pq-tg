from aiogram import F, Router, enums, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.settings import SettingsActions, keyboards
from utils import database

from . import RecordActions
from . import keyboards as record_keyboards

router = Router(name="record:start")


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.RECORD))
@flags.database("gen_settings")
async def start_handler(
    query: types.CallbackQuery,
    main_settings: database.models.MainSettings,
    gen_settings: database.models.GenSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    actions: dict[RecordActions, bool] = {
        RecordActions.MESSAGES: gen_settings.with_messages,
        RecordActions.STICKERS: gen_settings.with_stickers,
    }

    if query.message.chat.type != enums.ChatType.PRIVATE:
        actions.update(
            {
                RecordActions.MEMBERS: main_settings.with_members,
            },
        )

    content = formatting.as_marked_section(
        formatting.Bold(_("I am recording some information about this chat.")),
        *(formatting.Text(formatting.Bold(action.keyboard), " — ", action.description, ".") for action in actions),
    )

    await query.message.edit_text(
        reply_markup=record_keyboards.switch_keyboard(actions),
        **content.as_kwargs(),
    )

    await query.answer()
