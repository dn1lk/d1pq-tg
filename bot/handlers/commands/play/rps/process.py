import secrets

from aiogram import F, Router, flags, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from . import RPSValues, keyboards

router = Router(name="rps:process")


def _parse_score(text: str | None, entities: list[types.MessageEntity] | None):
    if text and entities and len(entities) > 1:
        return (int(entity.extract_from(text)) for entity in entities[:2])
    return 0, 0


@router.callback_query(keyboards.RPSData.filter(F.value))
@flags.throttling("rps")
async def process_handler(query: types.CallbackQuery, callback_data: keyboards.RPSData) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    bot_value = secrets.choice(list(RPSValues))
    user_value = callback_data.value

    _loses, _wins = _parse_score(query.message.text, query.message.entities)

    if user_value is bot_value:
        _title = f"{bot_value}. " + secrets.choice(
            (
                _("Draw."),
                _("Same..."),
                _("Brr..."),
                _("The score does not changed."),
                _("We already think alike."),
            ),
        )
    elif user_value is bot_value.resolve:
        _wins += 1
        _title = f"{bot_value}! " + _("My win!")
    else:
        _loses += 1
        _title = f"{bot_value}. " + _("Eh, my defeat...")

    content = formatting.Text(
        _title,
        "\n\n",
        _("Score"),
        ": ",
        formatting.Bold(_loses),
        "-",
        formatting.Bold(_wins),
        ".\n",
        formatting.TextMention(query.from_user.first_name, user=query.from_user),
        ", ",
        _("play again?"),
    )

    if content.as_markdown() != query.message.md_text:
        await query.message.edit_text(reply_markup=query.message.reply_markup, **content.as_kwargs())

    await query.answer(_("Your choice: {user_value}").format(user_value=user_value))
