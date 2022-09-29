from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from . import DRAW_CARD
from .data import UnoData

router = Router(name='game:uno:inline')

command = '/play uno'
thumb_url = 'https://image.api.playstation.com/cdn/EP0001/CUSA04040_00/LRI3Rg5MKOi5AkefFaMcChNv5WitM7sz.png'


@router.inline_query(F.query.lower() == "uno")
async def inline_handler(inline: types.InlineQuery, state: FSMContext):
    data = await state.get_data()
    data_uno: dict | None = data.get('uno')

    if data_uno:
        data_uno: UnoData = UnoData(**data_uno)
        cards = data_uno.users.get(inline.from_user.id)

        if cards:
            answer = [
                types.InlineQueryResultCachedSticker(
                    id='draw',
                    sticker_file_id='CAACAgIAAxkBAAJ99mKgyaLsi0LGnwOdUI_DhzgN7H1CAAKWFgAC1gkJSZxwlQOpRW3PJAQ',
                    input_message_content=types.InputMessageContent(message_text=str(DRAW_CARD)),
                )
            ]
            answer.extend(
                [
                    types.InlineQueryResultCachedSticker(
                        id=str(enum),
                        sticker_file_id=card.file_id,
                    ) for enum, card in enumerate(cards)
                ]
            )
        else:
            answer = [
                types.InlineQueryResultArticle(
                    id='no_cards',
                    title=command,
                    input_message_content=types.InputMessageContent(message_text=_("Next time I'm with you!")),
                    description=_("State your desire to play."),
                    thumb_url=thumb_url,
                )
            ]
    else:
        answer = [
            types.InlineQueryResultArticle(
                id='no_game',
                title=command,
                input_message_content=types.InputMessageContent(message_text=command),
                description=_("Start a new game."),
                thumb_url=thumb_url,
            )
        ]

    await inline.answer(answer, is_personal=True, cache_time=0)
