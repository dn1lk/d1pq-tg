from aiogram import Router, F, types
from aiogram.filters import MagicData
from aiogram.utils.i18n import gettext as _

from . import DRAW_CARD
from .process import UnoData
from .process.middleware import UnoDataMiddleware

router = Router(name='game:uno:inline')
router.inline_query.outer_middleware(UnoDataMiddleware())

command = '/play uno'
thumb_url = 'https://image.api.playstation.com/cdn/EP0001/CUSA04040_00/LRI3Rg5MKOi5AkefFaMcChNv5WitM7sz.png'


@router.inline_query(F.query.lower() == "uno", MagicData(F.data_uno))
async def inline_handler(inline: types.InlineQuery, data_uno: UnoData):
    user_data = data_uno.users.get(inline.from_user.id)

    if user_data:
        answer = [
            types.InlineQueryResultCachedSticker(
                id='draw',
                sticker_file_id='CAACAgIAAxUAAWNTyJCPqf4Upyd2mc0hDDM-9UD5AALgHwACheugSmbCtLV865YXKgQ',
                input_message_content=types.InputMessageContent(message_text=DRAW_CARD.value),
            )
        ]
        answer.extend(
            [
                types.InlineQueryResultCachedSticker(
                    id=str(enum),
                    sticker_file_id=card.file_id,
                ) for enum, card in enumerate(user_data.cards)
            ]
        )
    else:
        answer = [
            types.InlineQueryResultArticle(
                id='no_cards',
                title=command,
                input_message_content=types.InputMessageContent(message_text=command),
                description=_("Join to the game."),
                thumb_url=thumb_url,
            )
        ]

    await inline.answer(answer, is_personal=True, cache_time=0)


@router.inline_query(F.query.lower() == "uno")
async def inline_no_data_handler(inline: types.InlineQuery):
    await inline.answer(
        [
            types.InlineQueryResultArticle(
                id='no_game',
                title=command,
                input_message_content=types.InputMessageContent(message_text=command),
                description=_("Start a new game."),
                thumb_url=thumb_url,
            )
        ],
        is_personal=True,
        cache_time=0,
    )
