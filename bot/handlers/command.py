from random import choices, choice, random
from re import split

from aiogram import Router, Bot, F, types, filters, flags, html
from aiogram.utils.i18n import I18n, gettext as _

from bot.utils import markov, balaboba
from . import NO_ARGS, get_username, get_commands
from .settings.commands import CustomCommandFilter

router = Router(name="commands")


@router.message(CustomCommandFilter('start', 'начать'))
async def start_handler(message: types.Message, commands: dict[str, tuple[types.BotCommand]], i18n: I18n):
    answer = _(
        "I am a text generator bot and in some cases a great conversationalist.\n\n"
        "If you write me a message or a command, something might happen.\n\n"
    )

    commands = get_commands(commands[i18n.current_locale][:2])
    await message.answer(answer + commands)


@router.message(CustomCommandFilter('settings', 'настройки'))
async def settings_handler(message: types.Message, bot: Bot):
    """set up the bot, настроить бота"""

    from .settings import get_setup_answer
    await message.answer(**await get_setup_answer(message, bot))


async def get_command_args(command: filters.CommandObject, i18n: I18n, **kwargs) -> dict:
    return {
        'command': command.command,
        'args': markov.gen(locale=i18n.current_locale, text=command.command, max_words=5, **kwargs).lower()
    }


@router.message(CustomCommandFilter('choose', 'выбери', magic=F.args))
async def choose_handler(message: types.Message, command: filters.CommandObject):
    """make a choice, сделать выбор"""

    chosen = choice(split(r'\W+or\W+|\W+или\W+|\W{2,}', command.args))
    await message.answer(_("I choose {choice}.").format(choice=html.bold(html.quote(chosen))))


@router.message(CustomCommandFilter('choose', 'выбери'))
@router.message(CustomCommandFilter('help', 'помощь', magic=F.args.in_(('choose', 'выбери'))))
@flags.throttling('gen')
@flags.chat_action("typing")
async def choose_no_args_handler(
        message: types.Message,
        i18n: I18n,
        command: filters.CommandObject,
        messages: list[str],
):
    message = await message.answer(html.bold(_("What to choose?")))

    from .settings.commands import get_args
    await message.answer(
        NO_ARGS.format(
            command=command.command,
            args=_(" or ").join(choices(get_args(i18n, messages), k=2))
        )
    )


@router.message(F.chat.type == 'private', CustomCommandFilter('who', 'кто'))
async def who_private_handler(message: types.Message):
    await message.answer(_("This command only works in <b>chats</b>, alas =("))


@router.message(CustomCommandFilter('who', 'кто', magic=F.args))
@flags.data('members')
async def who_chat_handler(
        message: types.Message,
        bot: Bot,
        command: filters.CommandObject,
        members: list[int] | None,
):
    """find the desired participant, найти участника чата по описанию"""

    if members and len(members) > 1:
        member = await bot.get_chat_member(message.chat.id, choice(members))
        answer = choice(
            (
                _("Hmmm, I think"),
                _("I guess"),
                _("Oh, I admit"),
                _("Maybe it's"),
                _("Wait! It's")
            )
        ) + f" {get_username(member.user)} {html.bold(html.quote(command.args))}"
    elif members:
        answer = (_("Oh, I don't know you guys... Give me a time."))
    else:
        answer = _(
            "<b>This command requires permission to record chat participants.</b>\n\n"
            "/settings - give permission."
        )

    await message.answer(answer)


@router.message(CustomCommandFilter('who', 'кто'))
@router.message(CustomCommandFilter('help', 'помощь', magic=F.args.in_(('who', 'кто'))))
@flags.throttling('gen')
@flags.chat_action("typing")
async def who_chat_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list[str],
):
    message = await message.answer(html.bold(_("Who???")))
    await message.answer(
        NO_ARGS.format(
            **await get_command_args(
                command,
                i18n,
                messages=messages)
        )
    )


@router.message(CustomCommandFilter('play', 'поиграем', magic=F.args))
async def game_handler(message: types.Message):
    """play in a game, сыграть в игру"""

    await message.answer(
        choice(
            (
                _("Ha! Invalid request, try again."),
                _("Luck is clearly NOT in your favor. You didn't guess the game!"),
                _("The game is not recognized. I'll give it another try!"),
                _("And here it is not. This game has a different name ;)."),
            )
        )
    )


@router.message(CustomCommandFilter('play', 'поиграем'))
@router.message(CustomCommandFilter('help', 'помощь', magic=F.args.in_(('play', 'поиграем'))))
async def game_no_args_handler(message: types.Message, command: filters.CommandObject):
    def get_bot_args(r: Router):
        for f in r.message._handler.filters:
            if isinstance(f.callback, CustomCommandFilter):
                yield f.callback.magic._operations[1].args[0][0]

        for r in r.sub_routers:
            if r:
                yield from get_bot_args(r)

    answer = html.bold(_("<b>And what do you want to play?</b>"))

    if random() > 0.5:
        answer += _("\n\nTry to guess the game by writing the right words right after the command.")
    else:
        args = list(get_bot_args(router.parent_router))
        answer += NO_ARGS.format(
            command=command.command,
            args=choice(args),
        )

    await message.answer(answer)


@router.message(CustomCommandFilter('question', 'вопросик', magic=F.args))
@flags.chat_action("typing")
async def question_handler(
        message: types.Message,
        yalm: balaboba.Yalm,
        command: filters.CommandObject,
        i18n: I18n,
):
    """answer the question, ответить на вопрос"""

    args = html.quote(command.args)
    message = await message.answer(_("Hm, {args}?\nOk, I need to think...").format(args=html.bold(args)))

    if len(command.args) < 20:
        answer = await yalm.gen(i18n.current_locale, ' '.join(set(choices(args.split(), k=3))), 8)
    else:
        answer = _("Let's do it sooner!")

    await message.answer(answer)


@router.message(CustomCommandFilter('question', 'вопросик'))
@router.message(CustomCommandFilter('help', 'помощь', magic=F.args.in_(('question', 'вопросик'))))
@flags.throttling('gen')
@flags.chat_action("typing")
async def question_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list[str],
):
    message = await message.answer(html.bold(_("So what's the question?")))
    await message.answer(
        NO_ARGS.format(
            **await get_command_args(
                command,
                i18n,
                messages=messages)
        )
    )


@router.message(CustomCommandFilter('history', 'короче'))
@flags.throttling('gen')
@flags.chat_action("typing")
async def history_handler(
        message: types.Message,
        yalm: balaboba.Yalm,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list[str],
):
    """tell a story, рассказать историю"""

    query = html.quote(command.args) if command.args else choice(messages or [_("history")])

    if random() > 0.5:
        answer = await yalm.gen(i18n.current_locale, query, 6)
    else:
        query = _("In short, {query}").format(query=query)
        answer = markov.gen(i18n.current_locale, messages, query, state_size=2, tries=150000, min_words=50)

    await message.answer(answer)


'''
@router.message(CustomCommandFilter('future', 'погадай', magic=F.args))
@flags.chat_action("typing")
async def future_handler(
        message: types.Message,
        yalm: balaboba.Yalm,
        command: filters.CommandObject,
        i18n: I18n,
):
    """predict the future, предсказать будущее"""

    await message.answer(await yalm.gen(i18n.current_locale, command.args, 10))


@router.message(CustomCommandFilter('future', 'погадай'))
@router.message(CustomCommandFilter('help', 'помощь', magic=F.args.in_(('future', 'погадай'))))
@flags.throttling('gen')
@flags.chat_action("typing")
async def future_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list[str],
):
    message = await message.answer(_("<b>On coffee grounds?</b>"))
    await message.answer(
        NO_ARGS.format(
            **await get_command_args(
                command,
                i18n,
                messages=messages)
        )
    )
'''


@router.message(CustomCommandFilter('help', 'помощь'))
async def help_handler(message: types.Message, commands: dict[str, tuple[types.BotCommand]], i18n: I18n):
    """get a list of main commands, получить список основных команд"""

    answer = _("List of my main commands - I only accept them together with the required request, in one message:\n\n")
    commands = get_commands(commands[i18n.current_locale][2:])
    await message.answer(answer + commands)

