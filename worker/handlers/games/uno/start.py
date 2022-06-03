from random import choice, choices

from aiogram import Router, F, types, Bot
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from worker import keyboards as k
from worker.handlers import USERNAME
from worker.handlers.games import GameState
from worker.handlers.games.uno.bot import gen_bot

router = Router(name='game_rps')


@router.callback_query(k.GamesData.filter(F.value == 'start'))
async def game_uno_start(query: types.CallbackQuery, bot: Bot, state: FSMContext):
    data: dict = (await state.get_data())['game_uno']

    if len(data) > 1:
        await query.message.delete_reply_markup()

        cards = (await bot.get_sticker_set('uno_cards')).stickers

        for user_id, user_name in data.items():
            data[user_id] = user_name, {sticker.file_unique_id: sticker.file_id for sticker in choices(cards, k=6)}

        user = choice(list(data))

        if user == bot.id:
            answer = _("Какая неожиданность, мой ход.")
        else:
            answer = _("{user}, твой ход.").format(user=USERNAME.format(id=user, name=data[user][0]))

        await query.message.answer(_("<b>Итак, начнём игру.</b>\n\n") + answer, reply_markup=k.game_uno_show_cards())

        await state.set_state(GameState.UNO)

        data = await gen_bot(query.message, bot, data, [user], {})
        print(data)
        await state.update_data({'game_uno': data})
    else:
        await query.answer(_("А с кем играть то? =)"))


@router.callback_query(k.GamesData.filter(F.value == 'join'))
async def game_uno_join(query: types.CallbackQuery, state: FSMContext):
    data: dict = (await state.get_data()).get('game_uno')

    if query.from_user.id in data:
        await query.answer(_("Ты уже участвуешь!"))
    else:
        await query.message.edit_text(
            query.message.html_text + '\n' + USERNAME.format(id=query.from_user.id, name=query.from_user.first_name),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Теперь участников стало на один больше!"))

        data[query.from_user.id] = query.from_user.first_name
        await state.update_data({'game_uno': data})


@router.callback_query(k.GamesData.filter(F.value == 'decline'))
async def game_uno_decline(query: types.CallbackQuery, state: FSMContext):
    data: dict = (await state.get_data()).get('game_uno')

    if query.from_user.id in data:
        await query.message.edit_text(
            query.message.html_text.replace(
                "\n" + USERNAME.format(id=query.from_user.id, name=query.from_user.first_name), ''
            ),
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Теперь участников стало на один меньше!"))

        del data[query.from_user.id]
        await state.update_data({'game_uno': data})
    else:
        await query.answer(_("Ты ещё не участвуешь!"))
