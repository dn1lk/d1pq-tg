from json import dumps
from typing import Optional

from aiogram import Router, Bot, F, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from worker import keyboards as k

router = Router(name="settings_data")
router.callback_query.filter(k.SettingsData.filter(F.name == 'data'))


@router.callback_query(k.SettingsData.filter(F.value == 'delete'))
async def settings_data_delete_handler(
        query: types.CallbackQuery,
        bot: Bot,
        state: Optional[FSMContext] = None
):
    await bot.sql.del_data(query.message.chat.id, state)
    await query.message.edit_text(_("<b>The data was successfully deleted.</b>"))


@router.callback_query(k.SettingsData.filter(F.value))
async def settings_data_two_handler(
        query: types.CallbackQuery,
        bot: Bot,
        callback_data: k.SettingsData,
        state: Optional[FSMContext] = None
):
    items = {
        'members': (
            _("Members"),
            dumps({str(query.from_user.id): query.from_user.first_name}),
            None),
        'messages': (
            _("Messages"),
            [],
            ['DECLINE']
        )
    }

    value = callback_data.value.split('-')

    if value[1] == 'yes':
        status = _("enabled")
        answer = items[value[0]][1]
    else:
        status = _("disabled")
        answer = items[value[0]][2]

    await bot.sql.set_data(query.message.chat.id, value[0], answer, state)
    await query.message.edit_text(
        text=_("<b>{item} recording {status}.</b>").format(item=items[value[0]][0], status=status)
    )


@router.callback_query()
@flags.data({'messages', 'members'})
@flags.chat_action("typing")
async def settings_data_one_handler(
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
