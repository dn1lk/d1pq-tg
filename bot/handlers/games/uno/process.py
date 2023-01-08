from random import choice, random

from aiogram import Bot, Router, F, types, flags
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.handlers import get_username
from bot.utils.timer import timer
from .misc import keyboards as k
from .misc.data import UnoSettings

router = Router(name='game:uno:process')


def get_user_ids(entities: list[types.MessageEntity]) -> list[int]:
    return [entity.user.id for entity in entities if entity.user]


async def start_timer(message: types.Message, bot: Bot, state: FSMContext):
    await start_handler(message, bot, state, get_user_ids(message.entities))


async def start_filter(query: types.CallbackQuery, state: FSMContext):
    user_ids = get_user_ids(query.message.entities)

    if query.from_user.id == user_ids[0]:
        await timer.cancel(timer.get_name(state, 'game'))
        return {'user_ids': user_ids}


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.START), start_filter)
@flags.timer('game')
async def start_handler(
        query: types.CallbackQuery | types.Message,
        bot: Bot,
        state: FSMContext,
        user_ids: list[int],
):
    message = query.message if isinstance(query, types.CallbackQuery) else query
    message = await message.delete_reply_markup()

    settings = UnoSettings.extract(message)

    if random() < 1 / len(user_ids):
        user_ids.append(bot.id)

        await message.edit_text(f'{message.html_text}\n{get_username(await bot.me())}')
        await message.answer(
            choice(
                (
                    _("I play too!"),
                    _("I'll play with you."),
                    _("I'm with you.")
                )
            )
        )

    from .misc.process import start
    await start(state, user_ids, settings)


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.JOIN))
async def join_handler(query: types.CallbackQuery):
    user_ids = get_user_ids(query.message.entities)

    if query.from_user.id in user_ids:
        await query.answer(_("You are already in the list!"))
    elif len(user_ids) == 10:
        await query.answer(_("The number of players is already 10 people.\nI can't write anymore."))
    else:
        await query.message.edit_text(
            f'{query.message.html_text}\n{get_username(query.from_user)}',
            reply_markup=query.message.reply_markup
        )

        await query.answer(_("Now there are one more players!"))


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.LEAVE))
async def leave_handler(query: types.CallbackQuery, state: FSMContext):
    user_ids = get_user_ids(query.message.entities)

    if query.from_user.id in user_ids:
        if len(user_ids) == 1:
            await timer.cancel(timer.get_name(state, 'game'))
            await query.message.edit_text(
                choice(
                    (
                        _("Nobody wants to play =(."),
                        _("And who is there to play with?"),
                    )
                )
            )

        else:
            html_text = query.message.html_text

            await query.message.edit_text(
                html_text.replace(f'\n{get_username(query.from_user)}', ''),
                reply_markup=query.message.reply_markup
            )

            await query.answer(_("Now there is one less player!"))
    else:
        await query.answer(_("You are not in the list yet!"))


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.START))
async def start_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Only {user} can start the game.").format(user=query.message.entities[7].user.first_name))


@router.callback_query(k.UnoKeyboard.filter(F.action == k.UnoActions.SETTINGS))
async def settings_no_owner_handler(query: types.CallbackQuery):
    await query.answer(_("Only {user} can set up the game.").format(user=query.message.entities[7].user.first_name))
