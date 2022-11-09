from aiogram import Router, F, types, html
from aiogram.utils.i18n import gettext as _

from bot.utils.database.context import DataBaseContext
from .misc.data import RecordData
from ..misc import keyboards as k

router = Router(name="settings:record:start")


@router.callback_query(k.SettingsKeyboard.filter(F.action == k.SettingsAction.RECORD))
async def start_handler(query: types.CallbackQuery, db: DataBaseContext):
    answer = html.bold(_("I am recording some information about this chat.\n\n"))
    datas = {
        RecordData.MESSAGES: _("for more accurate and relevant message generation"),
    }

    if query.message.chat.type != 'private':
        datas.update(
            {
                RecordData.MEMBERS: _("to execute /who command"),
            }
        )

    for key, value in datas.items():
        answer += _("▪\t{data} - {description}.\n\n").format(data=html.bold(key.word), description=value)

    await query.message.edit_text(answer, reply_markup=k.record({key: await key.switch(db) for key in datas.keys()}))
    await query.answer()
