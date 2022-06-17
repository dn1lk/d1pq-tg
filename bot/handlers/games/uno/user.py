import asyncio
from random import choice

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot import keyboards as k
from bot.handlers import get_username
from .action import UnoAction
from .cards import UnoColors, draw_card
from .exceptions import UnoNoUsersException
from .data import UnoData

router = Router(name='game:uno:user')

DRAW_CARD = __("Take a card.")


@router.inline_query(F.query.lower() == "uno")
async def inline_handler(inline: types.InlineQuery, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoData = data.get('uno')

    thumb_url = 'https://image.api.playstation.com/cdn/EP0001/CUSA04040_00/LRI3Rg5MKOi5AkefFaMcChNv5WitM7sz.png'

    if data_uno:
        cards = data_uno.users.get(inline.from_user.id)

        if cards:
            answer = [
                         types.InlineQueryResultCachedSticker(
                             id=str(enum) + ':' + card.id,
                             sticker_file_id=card.file_id,
                         ) for enum, card in enumerate(cards)
                     ] + [
                         types.InlineQueryResultCachedSticker(
                             id='add' + ':' + draw_card.id,
                             sticker_file_id=draw_card.file_id,
                             input_message_content=types.InputMessageContent(message_text=str(DRAW_CARD)),
                         )
                     ]
        else:
            answer = [
                types.InlineQueryResultArticle(
                    id='no_cards',
                    title=_("Shall we play UNO?"),
                    input_message_content=types.InputMessageContent(message_text=_("Next time I'm with you!")),
                    description=_("State your desire to play."),
                    thumb_url=thumb_url,
                )
            ]
    else:
        answer = [
            types.InlineQueryResultArticle(
                id='no_game',
                title=_("Shall we play UNO?"),
                input_message_content=types.InputMessageContent(message_text='/play uno'),
                description=_("Start a new game."),
                thumb_url=thumb_url,
            )
        ]

    await inline.answer(answer, is_personal=True, cache_time=0)


@router.message(F.sticker.set_name == 'uno_cards')
async def user_handler(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    action_uno: UnoAction = UnoAction(message=message, state=state, data=data['uno'])

    card, accept, decline = action_uno.data.card_filter(message.from_user, message.sticker)

    if accept:
        for task in asyncio.all_tasks():
            if task.get_name() == str(action_uno.bot):
                task.cancel()
                break

        try:
            action_uno.data.timer_amount = 3
            await action_uno.prepare(card, accept)
        except UnoNoUsersException:
            await action_uno.end()

    elif decline:
        await action_uno.data.user_card_add(bot, message.from_user)
        await message.reply(decline)

    await state.update_data(uno=action_uno.data)


@router.message(F.text == DRAW_CARD)
async def add_card_handler(message: types.Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoData = data['uno']

    if message.from_user.id == data_uno.next_user.id:
        action_uno: UnoAction = UnoAction(message=message, state=state, data=data_uno)

        for task in asyncio.all_tasks():
            if task.get_name() == str(action_uno.bot):
                task.cancel()
                break

        await action_uno.draw_check()

        action_uno.data.current_special.skip = action_uno.data.current_user = message.from_user
        await action_uno.move(await action_uno.data.user_card_add(bot))

        await state.update_data(uno=action_uno.data)
    else:
        await message.reply(
            _(
                "Of course, I don't mind, but now it's {user}'s turn.\nWe'll have to wait =)."
            ).format(user=get_username(data_uno.next_user))
        )


@router.message(F.text.func(lambda text: any(emoji in text for emoji in (color.value[0] for color in UnoColors))))
async def get_color_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoData = data['uno']

    if data_uno.current_special.color and message.from_user.id == data_uno.current_user.id:
        data_uno.current_card.color = UnoColors[message.text.split()[0]]

        await message.answer(
            choice(
                (
                    _("Received."),
                    _("Changing color..."),
                    _("Some variety!"),
                )
            ),
            reply_markup=types.ReplyKeyboardRemove(),
        )

        action_uno = UnoAction(message=message, state=state, data=data_uno)

        await action_uno.move()
        await state.update_data(uno=action_uno.data)
    else:
        await message.answer(_("Good.\nWhen you'll get a black card, choose this color ;)."))


async def uno_answer(message: types.Message, state: FSMContext, user: types.User, action_uno: UnoAction):
    action_uno.data.uno_users_id.remove(user.id)

    for task in asyncio.all_tasks():
        if task.get_name() == str(action_uno.bot) + ':' + str(user.id) + ':' + 'uno':
            task.cancel()
            break

    if user.id == message.from_user.id:
        await message.reply(
            _("On reaction =)."),
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.reply(
            await action_uno.data.user_card_add(state.bot, user),
            reply_markup=types.ReplyKeyboardRemove()
        )

    await state.update_data(uno=action_uno.data)


@router.message(F.text.in_(k.UNO), F.reply_to_message)
async def uno_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action_uno: UnoAction = UnoAction(message=message, state=state, data=data['uno'])

    users = [message.reply_to_message.from_user]

    if message.reply_to_message.entities:
        users.extend(entities.user for entities in message.reply_to_message.entities if entities.user)

    for user in users:
        if user.id in action_uno.data.uno_users_id:
            await uno_answer(message, state, user, action_uno)
            break
    else:
        await message.reply(_("Nope."))


@router.message(F.text.in_(k.UNO), F.chat.type == 'private')
async def uno_private_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    action_uno: UnoAction = UnoAction(message=message, state=state, data=data['uno'])

    for user in message.from_user, await state.bot.get_me():
        if user.id in action_uno.data.uno_users_id:
            await uno_answer(message, state, user, action_uno)
            break
    else:
        await message.reply(_("Nope."))


@router.poll_answer()
async def poll_kick_handler(poll_answer: types.PollAnswer, bot: Bot, state: FSMContext):
    data = await state.get_data()
    data_uno: UnoData = data['uno']

    if poll_answer.option_ids == [0] and poll_answer.poll_id in data_uno.polls_kick:
        data_uno.polls_kick[poll_answer.poll_id].amount += 1

        if data_uno.polls_kick[poll_answer.poll_id].amount >= (len(data_uno.users) - 1) / 2:
            await bot.delete_message(state.key.chat_id, data_uno.polls_kick[poll_answer.poll_id].message_id)
            message = await bot.send_message(
                state.key.chat_id,
                _("{user} is kicked from the game.").format(
                    user=get_username(
                        (
                            await bot.get_chat_member(
                                state.key.chat_id,
                                data_uno.polls_kick[poll_answer.poll_id].user_id
                            )
                        ).user
                    )
                )
            )

            try:
                await data_uno.user_remove(state, data_uno.polls_kick.pop(poll_answer.poll_id).user_id)
            except UnoNoUsersException:
                action = UnoAction(message, state, data_uno)
                data_uno = await action.end()

        await state.update_data(uno=data_uno)
