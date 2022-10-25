from enum import Enum
from random import choice

from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from . import keyboards as k
from .. import get_username

router = Router(name='game:rps')


class RPSVars(str, Enum):
    rock = "🪨"
    scissors = "✂"
    paper = "📜"

    @property
    def word(self) -> str:
        items = {
            self.rock: _("Rock"),
            self.scissors: _("Scissors"),
            self.paper: _("Paper"),
        }

        return f'{self} {items[self]}'

    @property
    def resolve(self):
        items = {
            self.rock: self.scissors,
            self.scissors: self.paper,
            self.paper: self.rock,
        }

        return items.get(self)


@router.callback_query(k.Games.filter(F.game == 'rps'))
@flags.throttling('rps')
async def answer_handler(query: types.CallbackQuery, callback_data: k.Games):
    bot_var: RPSVars = choice(*RPSVars)
    user_var: RPSVars = RPSVars(callback_data.value)

    await query.answer(_("Your choice: {user_var}").format(user_var=user_var.word))

    loses, wins = (
        int(entity.extract_from(query.message.text)) for entity in query.message.entities[-2:]
    ) if len(query.message.entities) > 1 else (0, 0)

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

    score = _("Score: {loses}-{wins}.\nPlay again?").format(loses=html.bolt(loses), wins=html.bolt(wins))
    await query.message.edit_text(
        f'{bot_var.word}! {get_username(query.from_user)}, {result}\n\n{score}',
        reply_markup=k.rps_show_vars()
    )
