from typing import List

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.handlers import get_username

from .action import UnoAction, UnoNoUsersException
from .manager import UnoManager
from .cards import UnoColors, UnoCard

router = Router(name='game:uno:user')


DRAW_CARD = __("Беру карту.")


async def uno_timeout(message: types.Message, bot: Bot, state: FSMContext, data_uno: UnoManager):
    await message.reply(
        _(
            "Время вышло. {user} берёт дополнительную карту."
        ).format(user=get_username(data_uno.now_user))
    )

    await data_uno.add_card(bot, state, data_uno.now_user)
    await data_uno.next_user(bot, message.chat)

    await state.update_data(uno=data_uno)


@router.inline_query(F.query.lower().in_(('uno', 'уно')), state='*')
async def uno_inline(inline: types.InlineQuery, state: FSMContext):
    data = await state.get_data()
    uno_cards: List[UnoCard] = data.get('uno_cards')

    if uno_cards:
        answer = [
            types.InlineQueryResultCachedSticker(
                id=str(enum) + ':' + card.id,
                sticker_file_id=card.file_id
            ) for enum, card in enumerate(uno_cards)
        ] + [
            types.InlineQueryResultCachedSticker(
                id='add:AgADlhYAAtYJCUk',
                sticker_file_id='CAACAgIAAxkBAAJ99mKgyaLsi0LGnwOdUI_DhzgN7H1CAAKWFgAC1gkJSZxwlQOpRW3PJAQ',
                input_message_content=types.InputMessageContent(message_text=str(DRAW_CARD))
            )
        ]
    else:
        answer = [
            types.InlineQueryResultArticle(
                id='no_game',
                title=_("Сыграем в UNO?"),
                input_message_content=types.InputMessageContent(message_text='/play uno'),
                description=_("Инициировать новую игру."),
                thumb_url='https://upload.wikimedia.org/wikipedia/commons/f/f9/UNO_Logo.svg'
            )
        ]

    await inline.answer(answer, is_personal=True, cache_time=0)


@router.message(F.sticker.set_name == 'uno_cards')
async def uno_user(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno = UnoAction(message, bot, state, data.pop('uno'))

    data_uno.data.now_user_cards = await data_uno.data.get_now_user_cards(bot, state, message.from_user)
    card, action, decline = await data_uno.data.filter_card(bot, message.chat, message.from_user, message.sticker)
    if action:
        try:
            await data_uno.update(card, action)
        except UnoNoUsersException:
            await data_uno.remove()

    elif decline:
        await data_uno.data.add_card(bot, state, message.from_user)
        await message.answer(decline)

    await state.update_data(uno=data_uno.data)


@router.message(F.text == DRAW_CARD)
async def uno_add_card(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoAction = UnoAction(message, bot, state, data['uno'])

    if message.from_user.id == data_uno.data.now_user.id:
        data_uno.data.now_user_cards = await data_uno.data.get_now_user_cards(bot, state, message.from_user)
        await data_uno.next(await data_uno.data.add_card(bot, state))
        await state.update_data(uno=data_uno.data)
    else:
        await message.reply(
            _(
                "Я, конечно, не против, но сейчас очередь {user}. Придётся подождать =)."
            ).format(user=get_username(data_uno.data.now_user))
        )


@router.message(F.text.func(lambda text: any(emoji in text for emoji in (color.value[0] for color in UnoColors))))
async def uno_color(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoAction = UnoAction(message, bot, state, data['uno'])

    data_uno.data.now_card.color = UnoColors[message.text.split()[0]]
    await data_uno.move()

    await state.update_data(uno=data_uno.data)
