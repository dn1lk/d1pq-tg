from abc import ABCMeta, abstractmethod

from aiogram import F, Router, flags, types
from aiogram.handlers import CallbackQueryHandler
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import database
from utils.database.types import JsonList

from . import RecordActions, keyboards
from .misc.helpers import clear_data
from .misc.keyboards import RecordData

router = Router(name="record:update")


class UpdateBase(CallbackQueryHandler, metaclass=ABCMeta):
    @abstractmethod
    async def update_data(self) -> None:
        raise NotImplementedError

    @property
    def record_data(self) -> RecordData:
        return self.data["callback_data"]

    async def handle(self) -> None:
        assert isinstance(self.event.message, types.Message), "wrong message"

        await self.update_data()

        content = formatting.Text(
            self.record_data.action.keyboard,
            " ",
            _("recording is"),
            " ",
            formatting.Bold(_("disabled") if self.record_data.to_blocked else _("enabled")),
            ".",
        )

        await self.event.message.edit_text(**content.as_kwargs())
        await self.event.answer()


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.MESSAGES))
@flags.database("gen_settings")
class UpdateMessagesHandler(UpdateBase):
    async def update_data(self) -> None:
        gen_settings: database.GenSettings = self.data["gen_settings"]

        gen_settings.messages = None if self.record_data.to_blocked else JsonList()
        await gen_settings.save()


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.STICKERS))
@flags.database("gen_settings")
class UpdateStickersHandler(UpdateBase):
    async def update_data(self) -> None:
        gen_settings: database.GenSettings = self.data["gen_settings"]

        gen_settings.stickers = None if self.record_data.to_blocked else JsonList()
        await gen_settings.save()


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.MEMBERS))
class UpdateMembersHandler(UpdateBase):
    async def update_data(self) -> None:
        main_settings: database.MainSettings = self.data["gen_settings"]

        main_settings.members = None if self.record_data.to_blocked else JsonList([self.event.from_user.id])
        await main_settings.save()


@router.callback_query(keyboards.RecordData.filter(F.action == RecordActions.DELETE))
@flags.database(("gen_settings", "gpt_settings"))
async def delete_handler(
    query: types.CallbackQuery,
    main_settings: database.MainSettings,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
) -> None:
    assert isinstance(query.message, types.Message), "wrong message"

    await clear_data(main_settings, gen_settings, gpt_settings)

    content = formatting.Bold(_("Records was successfully deleted."))
    await query.message.edit_text(**content.as_kwargs())
    await query.answer()
