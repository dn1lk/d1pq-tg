from aiogram import F, Router, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.settings import SettingsActions, keyboards

from . import GPTOptionsActions
from . import keyboards as gpt_keyboards

router = Router(name="gpt:other")


@router.callback_query(keyboards.SettingsData.filter(F.action == SettingsActions.GPT))
@router.callback_query(gpt_keyboards.GPTOptionsData.filter(F.action == GPTOptionsActions.BACK))
async def start_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    actions = {
        GPTOptionsActions.MAX_TOKENS,
        GPTOptionsActions.TEMPERATURE,
    }

    content = formatting.as_marked_section(
        formatting.Bold(_("Change GPT options.")),
        *(formatting.Text(formatting.Bold(action.keyboard), " — ", action.description, ".") for action in actions),
    )

    await query.message.edit_text(
        reply_markup=gpt_keyboards.actions_keyboard(actions),
        **content.as_kwargs(),
    )

    await query.answer()
