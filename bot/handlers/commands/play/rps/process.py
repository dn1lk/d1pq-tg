from random import choice

from aiogram import Router, F, types, flags, html
from aiogram.utils.i18n import gettext as _

from . import RPSValues, keyboards

router = Router(name='rps:process')


def _parse_score(message: types.Message):
    if len(message.entities) > 1:
        return (int(entity.extract_from(message.text)) for entity in message.entities[:2])
    return 0, 0


@router.callback_query(keyboards.RPSData.filter(F.value))
@flags.throttling('rps')
async def process_handler(query: types.CallbackQuery, callback_data: keyboards.RPSData):
    message = query.message

    bot_value = choice(list(RPSValues))
    user_value = callback_data.value

    loses, wins = _parse_score(message)

    if user_value is bot_value:
        result = ". " + choice(
            (
                _("Draw."),
                _("Same..."),
                _("Brr..."),
                _("The score does not changed."),
                _("We already think alike."),
            )
        )
    elif user_value is bot_value.resolve:
        wins += 1
        result = "! " + _("My win!")
    else:
        loses += 1
        result = ". " + _("Eh, my defeat...")

    answer = _(
        "{bot_value}{result}\n\n"
        "Score: {loses}-{wins}.\n"
        "{user}, play again?"
    ).format(
        bot_value=bot_value, result=result,
        loses=html.bold(loses), wins=html.bold(wins),
        user=query.from_user.mention_html()
    )

    await message.edit_text(answer, reply_markup=message.reply_markup)
    await query.answer(_("Your choice: {user_value}").format(user_value=user_value))
