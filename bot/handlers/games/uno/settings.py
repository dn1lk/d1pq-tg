from aiogram import Router, F, types
from aiogram.utils.i18n import gettext as _

from .data import UnoDifficulty
from .. import keyboards as k
from ... import get_username

router = Router(name='game:uno:settings')


def get_current_difficulty(message: types.Message):
    difficulty = message.entities[1]
    return message.text[difficulty.offset:difficulty.offset + difficulty.length]


@router.callback_query(k.Games.filter(F.value == 'difficulty'), F.from_user.id == F.message.entities[3].user.id)
async def difficulty_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.uno_difficulties(get_current_difficulty(query.message)))


async def difficulty_change_filter(query: types.CallbackQuery):
    return await k.Games.filter(F.value.in_(difficulty.value for difficulty in UnoDifficulty))(query)


@router.callback_query(difficulty_change_filter, F.from_user.id == F.message.entities[3].user.id)
async def difficulty_change_handler(query: types.CallbackQuery, callback_data: k.Games):
    await query.message.edit_text(
        query.message.html_text.replace(
            get_current_difficulty(query.message),
            callback_data.value,
        ),
        reply_markup=k.uno_start(),
    )


@router.callback_query(k.Games.filter(F.value == 'back'), F.from_user.id == F.message.entities[3].user.id)
async def difficulty_back_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.uno_start())


@router.callback_query()
async def difficulty_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Only {user} can settings the game.").format(user=query.message.entities[3].user.first_name))
