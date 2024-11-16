from aiogram import Router, types

from core import filters

from .misc.helpers import get_start_content

router = Router(name="start")


@router.message(filters.CommandStart())
async def start_handler(message: types.Message) -> None:
    assert message.from_user is not None, "wrong user"

    content = get_start_content(message.from_user)
    await message.answer(**content.as_kwargs())
