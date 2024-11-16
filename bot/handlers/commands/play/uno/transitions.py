from aiogram import Bot, F, Router, filters, flags, types
from aiogram.fsm.context import FSMContext

from handlers.commands.play import PlayStates
from handlers.transitions.group import my_is_not_admin_filter, remove_member
from utils import TimerTasks, database

from .misc.actions.base import finish, restart
from .misc.actions.kick import kick_for_kick
from .misc.data import UnoData
from .misc.data.settings.modes import UnoMode

router = Router(name="uno:transition")

router.chat_member.filter(PlayStates.UNO)
router.message.filter(PlayStates.UNO)


async def kick_user(
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    user: types.User,
    main_settings: database.MainSettings,
) -> None:
    data_uno = await UnoData.get_data(state)
    if data_uno is None:
        return

    if user.id in data_uno.players.playing:
        await kick_for_kick(bot, state, timer, data_uno, user)

        if len(data_uno.players) == 1:
            await finish(bot, state, timer, data_uno)
        elif len(data_uno.players.playing) == 1 and data_uno.settings.mode is UnoMode.WITH_POINTS:
            await restart(bot, state, timer, data_uno)

    await remove_member(main_settings, user.id)


@router.chat_member(filters.ChatMemberUpdatedFilter(filters.LEAVE_TRANSITION))
@flags.timer(cancelled=False)
async def leave_action_handler(
    event: types.ChatMemberUpdated,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    main_settings: database.MainSettings,
) -> None:
    await kick_user(bot, state, timer, event.new_chat_member.user, main_settings)


@router.message(F.left_chat_member, my_is_not_admin_filter)
@flags.timer(cancelled=False)
async def leave_message_handler(
    message: types.Message,
    bot: Bot,
    state: FSMContext,
    timer: TimerTasks,
    main_settings: database.MainSettings,
) -> None:
    assert message.left_chat_member is not None, "wrong user"
    await kick_user(bot, state, timer, message.left_chat_member, main_settings)
