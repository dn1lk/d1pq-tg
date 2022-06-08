from typing import Optional

from aiogram import Router, F, types, flags
from aiogram.utils.i18n import gettext as _

from bot import keyboards as k
from bot.utils.database.context import DataBaseContext

router = Router(name="settings:data")
router.callback_query.filter(k.SettingsData.filter(F.name == 'data'))


@router.callback_query(k.SettingsData.filter(F.value == 'delete'))
async def data_delete_handler(
        query: types.CallbackQuery,
        db: DataBaseContext,
):
    await db.clear()
    await query.message.edit_text(_("<b>The data was successfully deleted.</b>"))


@router.callback_query(k.SettingsData.filter(F.value))
async def data_update_handler(
        query: types.CallbackQuery,
        callback_data: k.SettingsData,
        db: DataBaseContext,
):
    value = callback_data.value.split('-')

    if value[0] == 'members':
        item = _("Members")
        data = [query.from_user.id], None

    else:
        item = _("Messages")
        data = [], ['DECLINE']

    if value[1] == 'yes':
        status = _("enabled")
        data = data[0]
    else:
        status = _("disabled")
        data = data[1]

    await db.set_data({value[0]: data})
    await query.message.edit_text(
        text=_("<b>{item} recording {status}.</b>").format(item=item, status=status)
    )


@router.callback_query()
@flags.data({'messages', 'members'})
@flags.chat_action("typing")
async def data_handler(
        query: types.CallbackQuery,
        messages: Optional[list] = None,
        members: Optional[dict] = None,
):
    answer = _(
        "<b>I am logging some information about this chat.</b>\n\n"
        "This is necessary for my correct work. What am I recording?\n\n"
        "- <b>message list</b> - for more accurate and relevant message generation.\nDefault: enabled.\n\n"
    )
    if query.message.chat.type != 'private':
        answer += _("- <b>list of participants</b> - to execute the /who command.\nDefault: disabled.\n\n")

    await query.message.edit_text(
        text=answer,
        reply_markup=k.data(query.message.chat.type, members, messages)
    )
