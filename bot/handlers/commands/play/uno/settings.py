from aiogram import F, Router, types
from aiogram.utils import formatting

from .misc import keyboards
from .misc.data.settings.additions import UnoAdd, UnoAddState
from .misc.data.settings.difficulties import UnoDifficulty
from .misc.data.settings.modes import UnoMode

router = Router(name="uno:settings")
router.callback_query.filter(F.from_user.id == F.message.entities[7].user.id)


async def answer_change(
    query: types.CallbackQuery,
    current_enum: UnoDifficulty | UnoMode | UnoAdd,
    next_enum: UnoDifficulty | UnoMode | UnoAdd,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    await query.message.edit_text(
        query.message.md_text.replace(
            formatting.Text(str(current_enum)).as_markdown(),
            formatting.Text(str(next_enum)).as_markdown(),
        ),
        reply_markup=query.message.reply_markup,
    )

    await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSettings.DIFFICULTY))
async def difficulty_change_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    current_difficulty = UnoDifficulty.extract(query.message)
    await answer_change(query, current_difficulty, current_difficulty.next)


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSettings.MODE))
async def mode_change_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    current_mode = UnoMode.extract(query.message)
    await answer_change(query, current_mode, current_mode.next)


@router.callback_query(keyboards.UnoData.filter(F.action.in_(UnoAdd)))
async def additive_change_handler(query: types.CallbackQuery, callback_data: keyboards.UnoData) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert isinstance(callback_data.action, UnoAdd), "wrong callback data"
    assert isinstance(callback_data.value, UnoAddState), "wrong callback data"

    current_add = callback_data.action
    current_add_state = callback_data.value
    next_add_state = current_add_state.next

    name_add = str(current_add)

    button = query.message.reply_markup.inline_keyboard[current_add.value][0]
    button.text = f"{next_add_state.button} {name_add.lower()}"
    button.callback_data = button.callback_data.replace(
        str(current_add_state.value),
        str(next_add_state.value),
    )

    await query.message.edit_text(
        query.message.md_text.replace(
            formatting.Text(name_add, ": ", formatting.Bold(current_add_state)).as_markdown(),
            formatting.Text(name_add, ": ", formatting.Bold(next_add_state)).as_markdown(),
        ),
        reply_markup=query.message.reply_markup,
    )

    await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.SETTINGS))
async def settings_open_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    await query.message.edit_reply_markup(reply_markup=keyboards.settings_keyboard(query.message))
    await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.BACK))
async def settings_back_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    await query.message.edit_reply_markup(reply_markup=keyboards.setup_keyboard())
    await query.answer()
