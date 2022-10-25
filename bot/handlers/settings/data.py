from aiogram import Router, F, types, flags, html
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.utils.database.context import DataBaseContext
from . import keyboards as k

router = Router(name="settings:data")


@router.callback_query(k.Settings.filter(F.name == 'delete'))
async def delete_handler(query: types.CallbackQuery, state: FSMContext, db: DataBaseContext):
    await db.clear()
    await state.clear()

    await query.message.edit_text(html.bold(_("The data was successfully deleted.")))
    await query.answer()


async def update(query: types.CallbackQuery, callback_data: k.Settings):
    answer = _("{item} recording is {status}.")
    await query.message.edit_text(
        answer.format(
            item=callback_data.name,
            status=html.bold(_("enabled") if callback_data.value else _("disabled"))
        )
    )

    await query.answer()


@router.callback_query(k.Settings.filter(F.name == __('Messages')))
async def messages_update_handler(query: types.CallbackQuery, callback_data: k.Settings, db: DataBaseContext):
    await db.set_data(messages=None if callback_data.value else ["decline"])
    await update(query, callback_data)


@router.callback_query(k.Settings.filter(F.name == __('Members')))
async def members_update_handler(query: types.CallbackQuery, callback_data: k.Settings, db: DataBaseContext):
    await db.set_data(members=[query.from_user.id] if callback_data.value else None)
    await update(query, callback_data)


@router.callback_query()
@flags.data({'messages', 'members'})
async def data_handler(
        query: types.CallbackQuery,
        messages: list | None = None,
        members: dict | None = None,
):
    answer = html.bold(_("I am recording some information about this chat.\n\n"))
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
        answer += _("- <b>{item} recording</b> - {description}.\n\n").format(item=key, description=value[0])

    await query.message.edit_text(answer, reply_markup=k.data(**datas))
    await query.answer()
