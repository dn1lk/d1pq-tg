from functools import lru_cache

from aiogram import Bot, Router, enums, types
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands.settings import keyboards

router = Router(name="other")


@lru_cache(maxsize=2)
def transcript_locale(locale: str) -> str:
    match locale:
        case "ru":
            transcript_locale = "Русский"
        case "en":
            transcript_locale = "English"
        case _:
            msg = f"Unknown locale: {locale}"
            raise TypeError(msg)

    return transcript_locale


async def get_start_content(message: types.Message, bot: Bot) -> dict:
    if message.chat.type == enums.ChatType.PRIVATE:
        _chat = _("dialogue")
    else:
        _admins = formatting.as_line(
            *(
                formatting.TextMention(admin.user.first_name, user=admin.user)
                for admin in await bot.get_chat_administrators(message.chat.id)
            ),
            sep=",",
        )

        _chat = formatting.Text(_("chat — only for"), " ", _admins)

    content = formatting.Text(_("My settings of this"), " ", _chat, ":")
    return {
        "reply_markup": keyboards.actions_keyboard(),
        **content.as_kwargs(),
    }
