from enum import Enum, auto

from aiogram import Router, F, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

from bot import filters
from .misc import keyboards as k


UPDATE = __("\n\nUpdate:")
UPDATE_AGAIN = __("\n\nUpdate again:")

router = Router(name='settings')


class Settings(Enum):
    def _generate_next_value_(name, *args):
        return name.lower()

    COMMAND = auto()
    LOCALE = auto()
    CHANCE = auto()
    ACCURACY = auto()
    RECORD = auto()

    BACK = auto()

    @property
    def word(self) -> str:
        match self:
            case self.COMMAND:
                return _('Add command')
            case self.LOCALE:
                return _('Change language')
            case self.CHANCE:
                return _('Change generation chance')
            case self.ACCURACY:
                return _('Change generation accuracy')
            case self.RECORD:
                return _('Change record policy')

            case self.BACK:
                return _("Back")

        raise TypeError("Incorrect settings action")


class SettingsStates(StatesGroup):
    COMMAND = State()


@router.callback_query(k.SettingsKeyboard.filter(F.action), filters.AdminFilter(is_admin=False))
async def no_admin_handler(query: types.CallbackQuery):
    await query.answer(_("Only for administrators."))


def setup():
    from .accuracy import router as accuracy_rt
    from .chance import router as chance_rt
    from .locale import router as locale_rt
    from .other import router as other_rt

    sub_routers = (
        accuracy_rt,
        chance_rt,
        locale_rt,
        other_rt,
    )

    for sub_router in sub_routers:
        router.include_router(sub_router)

    from .commands import setup as command_st
    from .record import setup as record_st

    command_st(router)
    record_st(router)

    return router
