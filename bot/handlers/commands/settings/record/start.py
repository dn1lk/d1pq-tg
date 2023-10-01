from aiogram import Router, F, types, enums, html, flags
from aiogram.utils.i18n import gettext as _

from core.utils import database
from . import RecordActions
from .. import SettingsActions, keyboards

router = Router(name="record:start")


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.RECORD))
@flags.database('gen_settings')
async def start_handler(
        query: types.CallbackQuery,
        main_settings: database.MainSettings,
        gen_settings: database.GenSettings,
):
    answer = html.bold(_("I am recording some information about this chat.\n\n"))
    actions = {
        RecordActions.MESSAGES: gen_settings.messages,
        RecordActions.STICKERS: gen_settings.stickers,
    }

    if query.message.chat.type != enums.ChatType.PRIVATE:
        actions.update({
            RecordActions.MEMBERS: main_settings.members,
        })

    for action, value in actions.items():
        answer += f'▪ {html.bold(action.keyboard)} — {action.description}.\n'

    await query.message.edit_text(answer, reply_markup=keyboards.record_keyboard(actions))
    await query.answer()
