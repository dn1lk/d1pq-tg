from random import choice

from aiogram import Router, F, types, html
from aiogram.utils.i18n import gettext as _

from .misc import keyboards as k
from .misc.data import RPSData
from ... import get_username

router = Router(name='game:rps:process')


@router.callback_query(k.RPSKeyboard.filter(F.var))
async def process_handler(query: types.CallbackQuery, callback_data: k.RPSKeyboard):
    bot_var: RPSData = choice(tuple(RPSData))
    user_var: RPSData = callback_data.var

    if len(query.message.entities) > 1:
        loses, wins = (int(entity.extract_from(query.message.text)) for entity in query.message.entities[-2:])
    else:
        loses, wins = 0, 0

    if bot_var is user_var:
        wins += 1
        loses += 1
        result = _("draw.")
    elif bot_var.resolve is user_var:
        wins += 1
        result = _("my win!")
    else:
        loses += 1
        result = _("my defeat...")

    score = _("Score: {loses}-{wins}.\nPlay again?").format(loses=html.bold(loses), wins=html.bold(wins))
    await query.message.edit_text(
        f'{bot_var.word}! {get_username(query.from_user)}, {result}\n\n{score}',
        reply_markup=query.message.reply_markup
    )

    await query.answer(_("Your choice: {user_var}").format(user_var=user_var.word))
