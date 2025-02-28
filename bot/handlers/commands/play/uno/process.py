import asyncio
import secrets

from aiogram import Bot, F, Router, flags, types
from aiogram.fsm.context import FSMContext
from aiogram.utils import formatting
from aiogram.utils.i18n import gettext as _

from utils import TimerTasks

from . import MAX_PLAYERS
from .misc import keyboards
from .misc.data import UnoData
from .misc.data.settings import UnoSettings

router = Router(name="uno:process")


def get_users(entities: list[types.MessageEntity]) -> list[types.User]:
    return [entity.user for entity in entities if entity.user]


def add_user(message: types.Message, user: types.User) -> str:
    return f"{message.md_text}\n{formatting.TextMention(user.first_name, user=user).as_markdown()}"


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.JOIN))
async def join_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert query.message.entities is not None, "wrong entities"

    users = get_users(query.message.entities)

    if any(query.from_user.id == user.id for user in users):
        await query.answer(_("You are already in the list!"))
    elif len(users) == MAX_PLAYERS:
        await query.answer(_("There are too many players."))
    else:
        await query.message.edit_text(
            add_user(query.message, query.from_user),
            reply_markup=query.message.reply_markup,
        )

        await query.answer(_("Now there are one more players!"))


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.LEAVE))
@flags.timer(cancelled=False)
async def leave_handler(query: types.CallbackQuery, state: FSMContext, timer: TimerTasks) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert query.message.entities is not None, "wrong entities"

    users = get_users(query.message.entities)
    for user in users:
        if query.from_user.id != user.id:
            continue

        if len(users) == 1:
            del timer[state.key]

            content = formatting.Text(
                secrets.choice(
                    (
                        _("Nobody wants to play. 😢"),
                        _("And who is there to play with?"),
                    ),
                ),
            )

            await query.message.edit_text(**content.as_kwargs())
        else:
            await query.message.edit_text(
                query.message.md_text.replace(
                    f"\n{formatting.TextMention(user.first_name, user=user).as_markdown()}",
                    "",
                ),
                reply_markup=query.message.reply_markup,
            )

            await query.answer(_("Now there is one less player!"))

        break
    else:
        await query.answer(_("You are not in the list yet!"))


async def start_timer(message: types.Message, bot: Bot, state: FSMContext, timer: TimerTasks) -> None:
    assert isinstance(message, types.Message), "wrong message"
    assert message.entities is not None, "wrong entities"

    await asyncio.sleep(180)
    await start_handler(message, bot, state, timer, get_users(message.entities))


def start_filter(query: types.CallbackQuery) -> dict[str, list[types.User]] | bool:
    assert isinstance(query.message, types.Message), "wrong message"
    assert query.message.entities is not None, "wrong entities"

    users = get_users(query.message.entities)

    if query.from_user.id == users[0].id:
        return {"users": users}
    return False


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.START), start_filter)
@flags.timer
async def start_handler(
    query: types.CallbackQuery | types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    users: list[types.User],
) -> None:
    message = query.message if isinstance(query, types.CallbackQuery) else query
    assert isinstance(message, types.Message), "wrong message"

    message = await message.delete_reply_markup()
    assert isinstance(message, types.Message), "wrong message"

    settings = UnoSettings.extract(message)

    if secrets.randbelow(10) / 10 < 1 / len(users):
        user_bot = await bot.me()
        users.append(user_bot)

        await message.edit_text(add_user(message, user_bot))

        content = formatting.Text(
            secrets.choice(
                (
                    _("I play too!"),
                    _("I'll play with you."),
                    _("I'm with you."),
                ),
            ),
        )

        await message.answer(**content.as_kwargs())

    user_ids = [user.id for user in users]
    data_uno = await UnoData.setup(bot, state, user_ids, settings)

    from .misc.actions.base import start

    await start(bot, state, timer, data_uno)


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.START))
async def start_no_owner_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert query.message.entities is not None, "wrong entities"

    _user = query.message.entities[7].user.first_name
    await query.answer(_("Only {user} can start the game.").format(user=_user))


@router.callback_query(keyboards.UnoData.filter(F.action == keyboards.UnoSetup.SETTINGS))
async def settings_no_owner_handler(query: types.CallbackQuery) -> None:
    assert isinstance(query.message, types.Message), "wrong message"
    assert query.message.entities is not None, "wrong entities"

    _user = query.message.entities[7].user.first_name
    await query.answer(_("Only {user} can set up the game.").format(user=_user))
