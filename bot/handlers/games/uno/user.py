from random import shuffle

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot.handlers import get_username

from .action import UnoAction, UnoNoUsersException
from .manager import UnoManager
from .cards import UnoColors

router = Router(name='game:uno:user')


async def uno_timeout(message: types.Message, bot: Bot, state: FSMContext, data_uno: UnoManager):
    await message.reply(
        _(
            "Время вышло. {user} берёт дополнительную карту."
        ).format(user=get_username(data_uno.now_user))
    )

    await data_uno.add_card(bot, data_uno.now_user)
    await data_uno.next_user(bot, message.chat)

    await state.update_data(uno=data_uno)


@router.inline_query()
async def uno_inline(inline: types.InlineQuery, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoManager = data.get('uno')

    if data_uno:
        cards = data_uno.users.get(inline.from_user.id)

        if cards:
            cards = [
                types.InlineQueryResultCachedSticker(
                    id=str(i) + ':' + card.id,
                    sticker_file_id=card.file_id
                ) for card, i in zip(cards, range(6))
            ]

            shuffle(cards)
            await inline.answer(cards, cache_time=0)
        else:
            await inline.answer(
                [
                    types.InlineQueryResultArticle(
                        id="no_user",
                        title=_("You are not playing"),
                        input_message_content=types.InputTextMessageContent(
                            message_text=_('Нужно дождаться окончания текущей игры, чтобы присоединиться к новой.')
                        )
                    )
                ]
            )
    else:
        await inline.answer(
            [
                types.InlineQueryResultArticle(
                    id="no_game",
                    title=_("Start the game!"),
                    input_message_content=types.InputTextMessageContent(
                        message_text=_('/play uno')
                    )
                )
            ]
        )


@router.message(F.sticker.set_name == 'uno_cards')
async def uno_user(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno = UnoAction(message, bot, data.pop('uno'))

    print('- user', data_uno.data.users.keys(), len(data_uno.data.users[data_uno.data.now_user.id]), data_uno.data.now_user.first_name, (data_uno.data.now_card.color, data_uno.data.now_card.emoji, data_uno.data.now_card.special) if data_uno.data.now_card else None, data_uno.data.now_special)

    card, action, decline = data_uno.data.filter_card(message.from_user, message.sticker)
    if action:
        data_uno.now_card = message.sticker

        try:
            await data_uno.update(card, action)

            print('- user:end', data_uno.data.users.keys(), len(data_uno.data.users[data_uno.data.now_user.id]), data_uno.data.now_user.first_name, (data_uno.data.now_card.color, data_uno.data.now_card.emoji, data_uno.data.now_card.special) if data_uno.data.now_card else None, data_uno.data.now_special)
        except UnoNoUsersException:
            return await data_uno.remove(state, data)

    elif decline:
        await data_uno.data.add_card(bot, message.from_user)
        await message.answer(decline)

    await state.update_data(uno=data_uno.data)


@router.message(F.text == __("Беру карту."))
async def uno_no_card(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoAction = UnoAction(message, bot, data['uno'])

    if message.from_user.id == data_uno.data.now_user.id:
        await data_uno.next(await data_uno.data.add_card(bot))
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
    data_uno: UnoAction = UnoAction(message, bot, data['uno'])

    data_uno.data.now_card.color = UnoColors[message.text.split()[2]]
    await data_uno.move()

    await state.update_data(uno=data_uno.data)
