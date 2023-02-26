from aiogram import Router, Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from . import DRAW_CARD
from .misc import UnoData
from .misc.middleware import UnoFSMContextMiddleware

router = Router(name='game:uno:inline')
router.inline_query.filter(F.query.lower() == "uno")
router.inline_query.middleware(UnoFSMContextMiddleware())

COMMAND = '/play uno'
THUMB_URL = 'https://image.api.playstation.com/cdn/EP0001/CUSA04040_00/LRI3Rg5MKOi5AkefFaMcChNv5WitM7sz.png'


@router.inline_query(F.query == 'uno')
async def show_cards_handler(inline: types.InlineQuery, bot: Bot, state: FSMContext):
    sticker_set = await bot.get_sticker_set('uno_by_bp1lh_bot')
    data_uno = await UnoData.get_data(state)
    next_offset = None

    if data_uno:
        if inline.from_user.id in data_uno.users:
            def get_cards():
                for enum, card in enumerate(user_cards[offset:offset + size]):
                    yield types.InlineQueryResultCachedSticker(
                        id=str(offset + enum),
                        sticker_file_id=card.file_id,
                    )

            user_cards = data_uno.users[inline.from_user.id]

            if inline.offset:
                offset = int(inline.offset)
                size = 50

                answer = list(get_cards())
            else:
                offset = 0
                size = 49

                answer = [
                    types.InlineQueryResultCachedSticker(
                        id='draw',
                        sticker_file_id=sticker_set.stickers[-3].file_id,
                        input_message_content=types.InputTextMessageContent(message_text=DRAW_CARD.value),
                    )
                ]

                answer.extend(get_cards())

            if len(answer) == 50:
                next_offset = str(offset + min(len(user_cards), size))

        else:
            answer = [
                types.InlineQueryResultArticle(
                    id='no_cards',
                    title=COMMAND,
                    input_message_content=types.InputTextMessageContent(message_text=COMMAND),
                    description=_("Join to the game."),
                    thumb_url=THUMB_URL,
                )
            ]

    else:
        answer = [
            types.InlineQueryResultArticle(
                id='no_game',
                title=COMMAND,
                input_message_content=types.InputTextMessageContent(message_text=COMMAND),
                description=_("Start a new game."),
                thumb_url=THUMB_URL,
            )
        ]

    await inline.answer(answer, cache_time=0, is_personal=True, next_offset=next_offset)
