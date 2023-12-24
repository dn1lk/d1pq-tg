from aiogram import Router, F, types, html
from aiogram.utils.i18n import gettext as _

from . import GPTOptionsActions, keyboards as gpt_keyboards
from .. import SettingsActions, keyboards

router = Router(name='gpt:other')


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.GPT))
@router.callback_query(gpt_keyboards.GPTOptionsData.filter(F.action == GPTOptionsActions.BACK))
async def start_handler(query: types.CallbackQuery):
    answer = _("<b>Update GPT completion options.</b>\n\n")

    actions = {
        GPTOptionsActions.MAX_TOKENS,
        GPTOptionsActions.TEMPERATURE,
    }

    answer += '\n'.join(f'▪ {html.bold(action.keyboard)} — {action.description}.' for action in actions)

    await query.message.edit_text(answer, reply_markup=gpt_keyboards.actions_keyboard(actions))
    await query.answer()
