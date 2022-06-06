from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from . import UnoManager, get_username, get_card, get_sticker
from .bot import gen, action_card

router = Router(name='game:uno:user')


async def game_uno_timeout(message: types.Message, bot: Bot, state: FSMContext, data_uno: UnoManager):
    await message.reply(
        _(
            "Время вышло. {user} берёт дополнительную карту."
        ).format(user=get_username(data_uno.now_user))
    )

    await data_uno.add_card(bot, data_uno.now_user)
    await data_uno.next_user(bot, message.chat)

    answer = await data_uno.move_queue(bot)
    if answer:
        await message.reply(**answer)
    else:
        data = await state.get_data()
        data_uno = await gen(message, bot, state, data, data_uno)

    await state.update_data(uno=data_uno)


@router.inline_query()
async def game_uno_inline(inline: types.InlineQuery, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoManager = data.get('uno')

    cards = data_uno.users.get(inline.from_user.id)

    if cards:
        await inline.answer(
            [
                types.InlineQueryResultCachedSticker(
                    id=str(i) + ':' + card.file_unique_id,
                    sticker_file_id=card.file_id
                ) for card, i in zip(cards, range(6))
             ],
            cache_time=0,
        )
    else:
        await inline.answer(
            [
                types.InlineQueryResultArticle(
                    id="no_game",
                    title=_("You are not playing"),
                    input_message_content=
                    types.InputTextMessageContent(
                        message_text=_('Нужно дождаться окончания текущей игры, чтобы присоединиться к новой.')
                    )
                )
            ]
        )


@router.message(F.sticker.set_name == 'uno_cards')
async def user(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoManager = data.pop('uno')
    print(list(data_uno.users), data_uno.now_user.id, data_uno.now_card, data_uno.now_special)

    card = get_card(get_sticker(message.sticker))

    action, decline = data_uno.filter_card(message.from_user, card)
    if action:
        data_uno = await action_card(message, bot, state, data, data_uno, card, action)
    elif decline:
        await data_uno.add_card(bot, message.from_user)
        await message.reply(decline)

    await state.update_data(uno=data_uno)


@router.message(F.text == __("Беру карту."))
async def game_uno_no_card(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoManager = data['uno']

    if message.from_user.id == data_uno.now_user.id:
        await data_uno.add_card(bot)
        await data_uno.next_user(bot, message.chat)

        answer = await data_uno.move_queue(bot)
        if answer:
            await message.reply(**answer)
        else:
            data_uno = await gen(message, bot, state, data, data_uno)
    else:
        await message.reply(
            _(
                "Я, конечно, не против, но сейчас очередь {user}. Придётся подождать =)."
            ).format(user=get_username(data_uno.now_user))
        )

    await state.update_data(uno=data_uno)
