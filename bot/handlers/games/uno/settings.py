from enum import Enum

from aiogram import Router, F, types
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from .. import keyboards as k

router = Router(name='game:uno:settings')


class UnoDifficulty(int, Enum):
    easy = 3
    normal = 2
    hard = 1

    @property
    def word(self) -> str:
        difficulties = {
            self.easy: _('slowpoke'),
            self.normal: _('common man'),
            self.hard: _('genius'),
        }

        return difficulties.get(self)


class UnoMode(int, Enum):
    fast = 0
    with_points = 1

    @property
    def word(self) -> str:
        modes = {
            self.fast: _('fast'),
            self.with_points: _('with points'),
        }

        return modes.get(self)


class UnoSettings(BaseModel):
    difficulty: UnoDifficulty
    mode: UnoMode


def extract_current_difficulty(message: types.Message) -> UnoDifficulty:
    difficulty_word = message.entities[1].extract_from(message.text)

    for difficulty in UnoDifficulty:
        if difficulty.word == difficulty_word:
            return difficulty


@router.callback_query(F.from_user.id == F.message.entities[4].user.id, k.UnoGame.filter(F.value == 'settings'))
async def settings_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.uno_settings(query.message))


@router.callback_query(
    F.from_user.id == F.message.entities[4].user.id,
    k.UnoGame.filter(F.value.in_([difficulty.name for difficulty in UnoDifficulty]))
)
async def difficulty_change_handler(query: types.CallbackQuery, callback_data: k.Games):
    await query.message.edit_text(
        query.message.html_text.replace(
            extract_current_difficulty(query.message).word,
            UnoDifficulty[callback_data.value].word,
        ),
        reply_markup=k.uno_start(),
    )


def extract_current_mode(message: types.Message) -> UnoMode:
    difficulty_word = message.entities[2].extract_from(message.text)

    for difficulty in UnoMode:
        if difficulty.word == difficulty_word:
            return difficulty


@router.callback_query(
    F.from_user.id == F.message.entities[4].user.id,
    k.UnoGame.filter(F.value.in_([mode.name for mode in UnoMode]))
)
async def mode_change_handler(query: types.CallbackQuery, callback_data: k.Games):
    await query.message.edit_text(
        query.message.html_text.replace(
            extract_current_mode(query.message).word,
            UnoMode[callback_data.value].word,
        ),
        reply_markup=k.uno_start(),
    )


@router.callback_query(F.from_user.id == F.message.entities[4].user.id, k.UnoGame.filter(F.value == 'back'))
async def settings_back_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.uno_start())


@router.callback_query()
async def settings_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Only {user} can customize the game.").format(
        user=query.message.entities[4].user.first_name)
    )
