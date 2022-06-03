from asyncio import sleep

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from worker import keyboards as k
from worker.handlers.games.uno import USERNAME, add_card, action_card, bonus_card, prep_user
from worker.handlers.games.uno.bot import gen_bot

router = Router(name='game_rps')


async def game_uno_timer(message: types.Message, bot: Bot, state: FSMContext, data: dict):
    await sleep(60)

    new_data = (await state.get_data()).get('game_uno')

    if new_data and new_data.get('user') == data['user']:
        await message.reply(
            _("Время вышло. {user} берёт дополнительную карту.").format(
                user=USERNAME.format(
                    id=data['user'][0],
                    name=data['users'][data['user'][0]][0]
                )
            )
        )

        users = await add_card(message.from_user.id, bot, data['users'])
        user = [await prep_user(message, bot, users, data['user'][0]), message.sticker.file_unique_id]

        data = await gen_bot(message, bot, users, user, data['bonuses'])

        await state.update_data({'game_uno': data})


@router.inline_query()
async def game_uno_inline(inline: types.InlineQuery, state: FSMContext):
    users, user, bonuses = (await state.get_data())['game_uno'].values()

    if users.get(inline.from_user.id):
        await inline.answer(
            [
                types.InlineQueryResultCachedSticker(
                    id=file_unique_id,
                    sticker_file_id=file_id
                ) for file_unique_id, file_id in users[inline.from_user.id][1].items()
             ],
            is_personal=True,
            cache_time=1,
        )


@router.message(F.sticker.set_name == 'uno_cards')
async def game_uno_action(message: types.Message, bot: Bot, state: FSMContext):
    users, user, bonuses = (await state.get_data())['game_uno'].values()
    action = await action_card(message.from_user.id, message.sticker.file_unique_id, users, user, bonuses)

    if action:
        user = [user[0], message.sticker.file_unique_id]
        del users[message.from_user.id][1][message.sticker.file_unique_id]

        users, user, bonuses = await bonus_card(message, bot, users, user, bonuses)
        user[0] = await prep_user(message, bot, users, user[0], action)
    else:
        await message.reply(
            _("Нет, эта неправильная карта. Штраф: ещё одна карта в твоей коллекции."),
            reply_markup=k.game_uno_show_cards()
        )

        users = await add_card(message.from_user.id, bot, users)

    data = await gen_bot(message, bot, users, user, bonuses)
    print(10, data)
    if user[0]:
        await state.update_data({'game_uno': data})
        await game_uno_timer(message, bot, state, data)
    else:
        await state.clear()


@router.message(F.text == __("Беру карту."))
async def game_uno_no_card(message: types.Message, bot: Bot, state: FSMContext):
    users, user, bonuses = (await state.get_data())['game_uno'].values()

    users = await add_card(message.from_user.id, bot, users)
    user[0] = await prep_user(message, bot, users, user[0])

    data = await gen_bot(message, bot, users, user, bonuses)
    await state.update_data({'game_uno': data})
