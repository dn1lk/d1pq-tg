from aiogram import Router, F, types
from aiogram.utils.i18n import gettext as _

from .data import UnoDifficulty
from .. import keyboards as k
from ... import get_username

router = Router(name='game:uno:settings')


def get_current_difficulty(message: types.Message) -> UnoDifficulty:
    difficulty_name = message.entities[1]
    difficulty_name = message.text[difficulty_name.offset:difficulty_name.offset + difficulty_name.length]
    
    for difficulty in UnoDifficulty:
        if difficulty.name == difficulty_name:
            return difficulty


@router.callback_query(F.from_user.id == F.message.entities[3].user.id, k.Games.filter(F.value == 'difficulty'))
async def difficulty_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.uno_difficulties(get_current_difficulty(query.message)))


@router.callback_query(F.from_user.id == F.message.entities[3].user.id, k.Games.filter(F.value.in_(list(UnoDifficulty))))
async def difficulty_change_handler(query: types.CallbackQuery, callback_data: k.Games):
    await query.message.edit_text(
        query.message.html_text.replace(
            get_current_difficulty(query.message).name,
            callback_data.name,
        ),
        reply_markup=k.uno_start(),
    )


@router.callback_query(F.from_user.id == F.message.entities[3].user.id, k.Games.filter(F.value == 'back'))
async def difficulty_back_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.uno_start())


@router.callback_query()
async def difficulty_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Only {user} can settings the game.").format(user=query.message.entities[3].user.first_name))
