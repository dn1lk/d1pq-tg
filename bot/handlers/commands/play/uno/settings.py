from aiogram import Router, F, types, html

from .misc import keyboards
from .misc.data.settings.additions import UnoAdd, UnoAddState
from .misc.data.settings.difficulties import UnoDifficulty
from .misc.data.settings.modes import UnoMode

router = Router(name='uno:settings')
router.callback_query.filter(F.from_user.id == F.message.entities[7].user.id)


async def answer_change(
        query: types.CallbackQuery,
        current_enum: UnoDifficulty | UnoMode | UnoAdd,
        next_enum: UnoDifficulty | UnoMode | UnoAdd,
):
    await query.message.edit_text(
        query.message.html_text.replace(str(current_enum), str(next_enum)),
        reply_markup=query.message.reply_markup,
    )
    await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSettings.DIFFICULTY))
async def difficulty_change_handler(query: types.CallbackQuery):
    current_difficulty = UnoDifficulty.extract(query.message)
    await answer_change(query, current_difficulty, current_difficulty.next)


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSettings.MODE))
async def mode_change_handler(query: types.CallbackQuery):
    current_mode = UnoMode.extract(query.message)
    await answer_change(query, current_mode, current_mode.next)


@router.callback_query(keyboards.UnoData.filter(F.action.in_(UnoAdd)))
async def additive_change_handler(query: types.CallbackQuery, callback_data: keyboards.UnoData):
    current_add: UnoAdd = callback_data.action
    current_add_state: UnoAddState = callback_data.value
    next_add_state: UnoAddState = current_add_state.next

    name_add = str(current_add)

    button = query.message.reply_markup.inline_keyboard[current_add.value][0]
    button.text = f'{next_add_state.button} {name_add.lower()}'
    button.callback_data = button.callback_data.replace(str(current_add_state.value), str(next_add_state.value))

    await query.message.edit_text(
        query.message.html_text.replace(
            f'{name_add}: {html.bold(current_add_state)}',
            f'{name_add}: {html.bold(next_add_state)}',
        ),
        reply_markup=query.message.reply_markup
    )

    await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.SETTINGS))
async def settings_open_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=keyboards.settings_keyboard(query.message))
    await query.answer()


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoActions.BACK))
async def settings_back_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=keyboards.setup_keyboard())
    await query.answer()
