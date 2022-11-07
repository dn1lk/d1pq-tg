from enum import Enum, EnumMeta

from aiogram import Router, F, types, html
from aiogram.utils.i18n import gettext as _
from pydantic import BaseModel

from .misc import keyboards as k

router = Router(name='game:uno:settings')
router.callback_query.filter(F.from_user.id == F.message.entities[7].user.id)


class UnoSettingsMeta(EnumMeta):
    def meta_extract(cls, message: types.Message, index: int):
        enum_word = UnoSettings.get(message.entities)[index].extract_from(message.text)

        for enum in cls:
            if enum.word == enum_word:
                return enum


class UnoDifficulty(int, Enum, metaclass=UnoSettingsMeta):
    easy = 5
    normal = 3
    hard = 1

    @property
    def word(self) -> str:
        words = {
            self.easy: _('slowpoke'),
            self.normal: _('common man'),
            self.hard: _('genius'),
        }

        return words.get(self)

    @classmethod
    def extract(cls, message: types.Message) -> "UnoDifficulty":
        return cls.meta_extract(message, 0)


class UnoMode(int, Enum, metaclass=UnoSettingsMeta):
    fast = 0
    with_points = 1

    @property
    def word(self) -> str:
        words = {
            self.fast: _('fast'),
            self.with_points: _('with points'),
        }

        return words.get(self)

    @classmethod
    def extract(cls, message: types.Message) -> "UnoMode":
        return cls.meta_extract(message, 1)


class UnoAdd(int, Enum, metaclass=UnoSettingsMeta):
    off = 0
    on = 1

    @property
    def word(self) -> str:
        words = {
            self.off: _("off"),
            self.on: _("on"),
        }

        return words.get(self)

    @classmethod
    def extract(cls, message: types.Message, n: int) -> "UnoAdd":
        return cls.meta_extract(message, 2 + n)

    @property
    def switcher(self) -> str:
        changers = {
            self.off: _("Disable"),
            self.on: _("Enable"),
        }

        return changers.get(self)

    @staticmethod
    def get_names():
        return (
            _('Stacking'),
            _('Seven-O'),
            _('Jump-in'),
        )


class UnoSettings(BaseModel):
    difficulty: UnoDifficulty
    mode: UnoMode

    stacking: UnoAdd
    seven_0: UnoAdd
    jump_in: UnoAdd

    @classmethod
    def extract(cls, message: types.Message) -> "UnoSettings":
        return cls(
            difficulty=UnoDifficulty.extract(message),
            mode=UnoMode.extract(message),
            stacking=UnoAdd.extract(message, 0),
            seven_0=UnoAdd.extract(message, 1),
            jump_in=UnoAdd.extract(message, 2),
        )

    @staticmethod
    def get(entities: list[types.MessageEntity]):
        return [entity for entity in entities if entity.type == 'bold'][1:-1]


@router.callback_query(k.UnoKeyboard.filter(F.action == 'settings'))
async def settings_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.settings(query.message))
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action.in_([difficulty.name for difficulty in UnoDifficulty])))
async def difficulty_change_handler(query: types.CallbackQuery, callback_data: k.UnoKeyboard):
    await query.message.edit_text(
        query.message.html_text.replace(
            UnoDifficulty.extract(query.message).word,
            UnoDifficulty[callback_data.action].word,
        ),
        reply_markup=k.start(),
    )
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action.in_([mode.name for mode in UnoMode])))
async def mode_change_handler(query: types.CallbackQuery, callback_data: k.UnoKeyboard):
    await query.message.edit_text(
        query.message.html_text.replace(
            UnoMode.extract(query.message).word,
            UnoMode[callback_data.action].word,
        ),
        reply_markup=k.start(),
    )
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action.in_([add.name for add in UnoAdd])))
async def additive_change_handler(query: types.CallbackQuery, callback_data: k.UnoKeyboard):
    new_add = UnoAdd[callback_data.action]
    old_add = UnoAdd.off if new_add else UnoAdd.on
    name = UnoAdd.get_names()[callback_data.value]

    await query.message.edit_text(
        query.message.html_text.replace(
            f'{name}: {html.bold(old_add.word)}',
            f'{name}: {html.bold(new_add.word)}',
        ),
        reply_markup=k.start(),
    )
    await query.answer()


@router.callback_query(k.UnoKeyboard.filter(F.action == 'back'))
async def settings_back_handler(query: types.CallbackQuery):
    await query.message.edit_reply_markup(k.start())
    await query.answer()
