from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from handlers.commands import CommandTypes
from handlers.commands.misc.types import PREFIX
from handlers.commands.play import PlayActions

from . import DRAW_CARD
from .misc.data import UnoData
from .misc.data.deck.base import STICKER_SET_NAME
from .misc.middleware import UnoMiddleware

router = Router(name="uno:inline")
router.inline_query.filter(F.query.lower().in_(PlayActions.UNO))

UnoMiddleware().setup(router)

COMMAND = f"{PREFIX}{CommandTypes.PLAY[0]} {PlayActions.UNO[0]}"
THUMB_URL = "https://image.api.playstation.com/cdn/EP0001/CUSA04040_00/LRI3Rg5MKOi5AkefFaMcChNv5WitM7sz.png"
PAGE_SIZE = 50


@router.inline_query()
async def show_cards_handler(inline: types.InlineQuery, bot: Bot, state: FSMContext) -> None:
    sticker_set = await bot.get_sticker_set(STICKER_SET_NAME)
    data_uno = await UnoData.get_data(state)
    next_offset = None

    if data_uno:
        player = data_uno.players.playing[inline.from_user.id]

        if player:

            def get_cards():
                for enum, card in enumerate(player.cards[offset : offset + size]):
                    yield types.InlineQueryResultCachedSticker(
                        id=str(offset + enum),
                        sticker_file_id=card.file_id,
                    )

            if inline.offset:
                offset = int(inline.offset)
                size = PAGE_SIZE

                content = list(get_cards())
            else:
                offset = 0
                size = PAGE_SIZE - 1

                content = [
                    types.InlineQueryResultCachedSticker(
                        id="draw",
                        sticker_file_id=sticker_set.stickers[-1].file_id,
                        input_message_content=types.InputTextMessageContent(
                            **formatting.Text(DRAW_CARD).as_kwargs(text_key="message_text"),
                        ),
                    ),
                    *get_cards(),
                ]

            if len(content) == PAGE_SIZE:
                next_offset = str(offset + min(len(player.cards), size))

        else:
            content = [
                types.InlineQueryResultArticle(
                    id="no_cards",
                    title=COMMAND,
                    input_message_content=types.InputTextMessageContent(
                        **formatting.Text(COMMAND).as_kwargs(text_key="message_text"),
                    ),
                    description=_("Join to the game."),
                    thumb_url=THUMB_URL,
                ),
            ]

    else:
        content = [
            types.InlineQueryResultArticle(
                id="no_game",
                title=COMMAND,
                input_message_content=types.InputTextMessageContent(
                    **formatting.Text(COMMAND).as_kwargs(text_key="message_text"),
                ),
                description=_("Start a new game."),
                thumb_url=THUMB_URL,
            ),
        ]

    await inline.answer(content, cache_time=0, is_personal=True, next_offset=next_offset)
