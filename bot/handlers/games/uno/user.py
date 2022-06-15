import asyncio

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot import keyboards as k
from bot.handlers import get_username
from .action import UnoAction
from .cards import UnoColors, draw_card
from .exceptions import UnoNoUsersException
from .manager import UnoManager

router = Router(name='game:uno:user')

DRAW_CARD = __("Беру карту.")


@router.inline_query(F.query.lower().in_(('uno', 'уно')))
async def inline_handler(inline: types.InlineQuery, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoManager = data.get('uno')

    if data_uno:
        cards = data_uno.users.get(inline.from_user.id)

        if cards:
            answer = [
                         types.InlineQueryResultCachedSticker(
                             id=str(enum) + ':' + card.id,
                             sticker_file_id=card.file_id
                         ) for enum, card in enumerate(cards)
                     ] + [
                         types.InlineQueryResultCachedSticker(
                             id='add' + ':' + draw_card.id,
                             sticker_file_id=draw_card.file_id,
                             input_message_content=types.InputMessageContent(message_text=str(DRAW_CARD))
                         )
                     ]
        else:
            answer = [
                types.InlineQueryResultArticle(
                    id='no_cards',
                    title=_("Сыграем в UNO?"),
                    input_message_content=types.InputMessageContent(message_text='В следующий раз я с вами!'),
                    description=_("Заявить о желании сыграть."),
                    thumb_url='https://upload.wikimedia.org/wikipedia/commons/f/f9/UNO_Logo.svg'
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
async def user_handler(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno = UnoAction(message=message, state=state, data=data.pop('uno'))

    card, accept, decline = await data_uno.data.card_filter(bot, message.chat.id, message.from_user, message.sticker)
    if accept:
        for task in asyncio.all_tasks():
            if task.get_name() == str(data_uno.bot):
                task.cancel()
                break

        try:
            await data_uno.prepare(card, accept)
        except UnoNoUsersException:
            await data_uno.end()

    elif decline:
        await data_uno.data.user_card_add(bot, message.from_user)
        await message.answer(decline)

    await state.update_data(uno=data_uno.data)


@router.message(F.text == DRAW_CARD)
async def add_card_handler(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoAction = UnoAction(message=message, state=state, data=data['uno'])

    if message.from_user.id == data_uno.data.next_user.id:
        data_uno.data.current_user = data_uno.data.next_user
        data_uno.data.next_user = await data_uno.data.user_next(bot, message.chat.id)
        await data_uno.move(await data_uno.data.user_card_add(bot))

        await state.update_data(uno=data_uno.data)
    else:
        await message.reply(
            _(
                "Я, конечно, не против, но сейчас очередь {user}. Придётся подождать =)."
            ).format(user=get_username(data_uno.data.current_user))
        )


@router.message(F.text.func(lambda text: any(emoji in text for emoji in (color.value[0] for color in UnoColors))))
async def get_color_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoAction = UnoAction(message=message, state=state, data=data['uno'])

    if data_uno.data.current_special.color and message.from_user.id == data_uno.data.current_user.id:
        data_uno.data.current_card.color = UnoColors[message.text.split()[0]]

        await data_uno.move()
        await state.update_data(uno=data_uno.data)
    else:
        await message.answer(_("Хорошо.\nКогда получишь специальную карту, выберешь этот цвет ;)."))


@router.message(F.text.in_(k.UNO), F.reply_to_message)
async def uno_handler(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoAction = UnoAction(message=message, state=state, data=data['uno'])

    if message.reply_to_message.from_user.id in data_uno.data.uno_users_id:
        data_uno.data.uno_users_id.remove(message.reply_to_message.from_user.id)

        if message.reply_to_message.from_user.id == message.from_user.id:
            await message.reply(_("На реакции =)."), reply_markup=types.ReplyKeyboardRemove())
        else:
            if message.reply_to_message.from_user.id == bot.id:
                for task in asyncio.all_tasks():
                    if task.get_name() == str(data_uno.bot) + ':' + 'uno':
                        task.cancel()
                        break

            await message.reply(
                await data_uno.data.user_card_add(bot, message.reply_to_message.from_user),
                reply_markup=types.ReplyKeyboardRemove()
            )

        await state.update_data(uno=data_uno.data)
    else:
        await message.answer(_("Сам ты уно!"))


@router.poll_answer()
async def poll_kick_handler(poll_answer: types.PollAnswer, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoManager = data['uno']

    if poll_answer.poll_id in data_uno.kick_polls.keys() and poll_answer.option_ids == [0]:
        data_uno.kick_polls[poll_answer.poll_id].amount += 1

        if data_uno.kick_polls[poll_answer.poll_id].amount >= len(data_uno.users) / 2:
            await bot.delete_message(state.key.chat_id, data_uno.kick_polls[poll_answer.poll_id].message_id)
            message = await bot.send_message(
                state.key.chat_id,
                _("{user} исключён из игры.").format(
                    user=get_username(
                        (
                            await bot.get_chat_member(
                                state.key.chat_id,
                                data_uno.kick_polls[poll_answer.poll_id].user_id
                            )
                        ).user
                    )
                )
            )

            try:
                await data_uno.user_remove(state, data_uno.kick_polls.pop(poll_answer.poll_id).user_id)
            except UnoNoUsersException:
                action = UnoAction(message, state, data_uno)
                data_uno = await action.end()

        await state.update_data(uno=data_uno)
