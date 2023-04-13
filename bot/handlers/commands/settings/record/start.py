from aiogram import Router, F, types, enums, html
from aiogram.utils.i18n import gettext as _

from bot.core.utils import database
from bot.handlers.commands.settings.record.misc.actions import RecordActions
from .. import SettingsActions, keyboards

router = Router(name="record:start")


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.RECORD))
async def start_handler(query: types.CallbackQuery, db: database.SQLContext):
    answer = html.bold(_("I am recording some information about this chat.\n\n"))
    datas = [RecordActions.MESSAGES]

    if query.message.chat.type != enums.ChatType.PRIVATE:
        datas.append(RecordActions.MEMBERS)

    for data in datas:
        answer += f'▪ {html.bold(data.keyboard)} - {data.description}.\n\n'

    await query.message.edit_text(
        answer,
        reply_markup=keyboards.record_keyboard(
            [(data, await data.switch(db, query.message.chat.id)) for data in datas]
        )
    )

    await query.answer()
