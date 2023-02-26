from aiogram import Router, F, types, html

from .misc import keyboards as k
from .misc.data import UnoDifficulty, UnoMode, UnoAdd

router = Router(name='game:uno:settings')
router.callback_query.filter(F.from_user.id == F.message.entities[7].user.id)


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.SETTINGS))
async def settings_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.settings(query.message))
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.DIFFICULTY))
async def difficulty_change_handler(query: types.CallbackQuery):
    current_mode = UnoDifficulty.extract(query.message)
    next_mode = UnoDifficulty.next(current_mode)

    await query.message.edit_text(
        query.message.html_text.replace(current_mode.word, next_mode.word),
        reply_markup=query.message.reply_markup,
    )
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.MODE))
async def mode_change_handler(query: types.CallbackQuery):
    current_mode = UnoMode.extract(query.message)
    next_mode = UnoMode.next(current_mode)

    await query.message.edit_text(
        query.message.html_text.replace(current_mode.word, next_mode.word),
        reply_markup=query.message.reply_markup,
    )
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action.in_(UnoAdd)))
async def additive_change_handler(query: types.CallbackQuery, callback_data: k.UnoKeyboard):
    current_add = callback_data.action
    next_add = UnoAdd.next(current_add)
    name = UnoAdd.get_names()[callback_data.value]

    button = query.message.reply_markup.inline_keyboard[2 + callback_data.value][0]
    button.text = f'{next_add.switcher} {name.lower()}'
    button.callback_data = button.callback_data.replace(str(current_add.value), str(next_add.value), 1)

    await query.message.edit_text(
        query.message.html_text.replace(
            f'{name}: {html.bold(current_add.word)}',
            f'{name}: {html.bold(next_add.word)}',
        ),
        reply_markup=query.message.reply_markup
    )

    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.BACK))
async def settings_back_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.setup())
    await query.answer()
