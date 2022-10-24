from aiogram import Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.utils.database.context import DataBaseContext
from . import keyboards as k

router = Router(name="settings:data")


@router.callback_query(k.Settings.filter(F.name == 'delete'))
async def delete_handler(query: types.CallbackQuery, state: FSMContext, db: DataBaseContext):
    await db.clear()
    await state.clear()

    await query.message.edit_text(_("<b>The data was successfully deleted.</b>"))


async def update(message: types.Message, callback_data: k.Settings):
    await message.edit_text(
        _("<b>{item} recording is {status}.</b>").format(
            item=callback_data.name,
            status=_("enabled") if callback_data.value else _("disabled")
        )
    )


@router.callback_query(k.Settings.filter(F.name == __('Messages')))
async def messages_update_handler(query: types.CallbackQuery, callback_data: k.Settings, db: DataBaseContext):
    await db.set_data(messages=None if callback_data.value else ["decline"])
    await update(query.message, callback_data)


@router.callback_query(k.Settings.filter(F.name == __('Members')))
async def members_update_handler(query: types.CallbackQuery, callback_data: k.Settings, db: DataBaseContext):
    await db.set_data(members=[query.from_user.id] if callback_data.value else None)
    await update(query.message, callback_data)


@router.callback_query()
@flags.data({'messages', 'members'})
async def data_handler(
        query: types.CallbackQuery,
        messages: list | None = None,
        members: dict | None = None,
):
    answer = _("<b>I am recording some information about this chat.</b>\n\n")

    datas = {
        _('Messages'): (_("for more accurate and relevant message generation"), messages == ['decline']),
    }

    if query.message.chat.type != 'private':
        datas.update(
            {
                _('Members'): (_("to execute /who command"), not members),
            }
        )

    for key, value in datas.items():
        answer += _("- <b>{item} recording</b> - {description}.").format(
            item=key,
            description=value[0]
        ) + "\n\n"

    await query.message.edit_text(answer, reply_markup=k.data(**datas))
