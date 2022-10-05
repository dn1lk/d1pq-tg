from random import choices, choice
from re import findall, split

from aiogram import Router, Bot, F, types, filters, flags
from aiogram.utils.i18n import I18n, gettext as _

from bot import filters as f
from bot.utils import markov, balaboba
from . import NO_ARGS, get_username, get_command_list
from .settings.commands.filter import CustomCommandFilter

router = Router(name="commands")


@router.message(~F.from_user.is_bot, f.LevenshteinFilter(lev={'hello', 'hey', 'здравствуйте', 'привет'}))
@router.message(CustomCommandFilter(commands=['start', 'начать'], ignore_case=True))
async def hello_handler(message: types.Message, bot: Bot, i18n: I18n):
    await message.answer(
        _(
            "Hello, {user}. "
            "I am a text generator bot and in some cases a great conversationalist.\n\n"
            "If you write me a message or a command, something might happen."
        ).format(user=get_username(message.from_user)) +
        "\n\n" +
        get_command_list(bot, i18n.current_locale, slice(2)),
    )


@router.message(CustomCommandFilter(commands=['settings', 'настройки'], ignore_case=True))
async def settings_handler(message: types.Message, bot: Bot):
    """set up the bot, настроить бота"""

    from .settings.other import get_answer

    await message.answer(**await get_answer(message.chat.id, message.from_user.id, bot))


@router.message(CustomCommandFilter(commands=['help', 'помощь'], ignore_case=True))
async def help_handler(message: types.Message, bot: Bot, i18n: I18n):
    """get a list of main commands, получить список основных команд"""

    await message.answer(
        _("List of my main commands - I only accept them together with the required request, in one message:") +
        "\n\n" +
        get_command_list(bot, i18n.current_locale, slice(2, None))
    )


async def get_command_args(command: filters.CommandObject, i18n: I18n, **kwargs) -> dict:
    return {
        'command': command.command,
        'args': (markov.gen(locale=i18n.current_locale, text=command.command, max_words=5, **kwargs)).lower()
    }


@router.message(CustomCommandFilter(commands=['choose', 'выбери'], ignore_case=True, magic=F.args))
async def choose_handler(
        message: types.Message,
        command: filters.CommandObject
):
    """make a choice, сделать выбор"""

    await message.answer(
        _("I choose <b>{choice}</b>.").format(choice=choice(split(r'\W+or\W+|\W+или\W+|\W+', command.args)))
    )


@router.message(CustomCommandFilter(commands=['choose', 'выбери'], ignore_case=True))
@flags.data('messages')
@flags.chat_action("typing")
async def choose_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list | None = None):
    message = await message.answer(_("<b>What to choose?</b>"))

    args = markov.get_base(i18n.current_locale, choice(markov.books)).parsed_sentences
    if messages:
        args = messages + args

    await message.answer(
        NO_ARGS.format(
            command=command.command,
            args=_("{args[0]} or {args[1]}").format(args=choices(findall(r'\w{4,}', str(args)), k=2))
        )
    )


@router.message(F.chat.type == 'private', CustomCommandFilter(commands=['who', 'кто'], ignore_case=True))
async def who_private_handler(message: types.Message):
    await message.answer(_("This command only works in <b>chats</b>, alas =(."))


@router.message(CustomCommandFilter(commands=['who', 'кто'], ignore_case=True, magic=F.args))
@flags.data('members')
async def who_chat_handler(
        message: types.Message,
        bot: Bot,
        command: filters.CommandObject,
        members: list | None = None,
):
    """find the desired participant, найти участника чата по описанию"""

    if members:
        if len(members) > 1:
            member = await bot.get_chat_member(message.chat.id, choice(members))
            answer = _("Hmmm, I think {user} {args}").format(
                user=get_username(member.user),
                args=command.args,
            )
        else:
            answer = (_("Oh, I don't know you guys... Give me a time."))
    else:
        answer = _(
            "<b>This command requires permission to record chat participants.</b>\n\n"
            "/settings - give permission."
        )

    await message.answer(answer)


@router.message(CustomCommandFilter(commands=['who', 'кто'], ignore_case=True))
@flags.data('messages')
@flags.chat_action("typing")
async def who_chat_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list | None = None,
):
    message = await message.answer(_("<b>Who???</b>"))
    await message.answer(
        NO_ARGS.format(
            **await get_command_args(
                command,
                i18n,
                messages=messages)
        )
    )


@router.message(CustomCommandFilter(commands=['play', 'поиграем'], ignore_case=True, magic=F.args))
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


@router.message(CustomCommandFilter(commands=['play', 'поиграем'], ignore_case=True))
async def game_no_args_handler(message: types.Message):
    await message.answer(
        _(
            "<b>And what do you want to play?</b>\n\n"
            "Try to guess the game by writing the right words right after the command."
        )
    )


@router.message(CustomCommandFilter(commands=['question', 'вопросик'], ignore_case=True, magic=F.args))
@flags.chat_action("typing")
async def question_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        yalm: balaboba.Yalm,
):
    """answer the question, ответить на вопрос"""

    message = await message.answer(_("Hm, {args}?\nOk, I need to think...").format(args=command.args))

    if len(command.args) < 20:
        answer = await yalm.gen(i18n.current_locale, command.args, 8)
    else:
        answer = _("Let's do it sooner!")

    await message.answer(answer)


@router.message(CustomCommandFilter(commands=['question', 'вопросик'], ignore_case=True))
@flags.data('messages')
@flags.chat_action("typing")
async def question_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list | None = None
):
    message = await message.answer(_("<b>So what's the question?</b>"))
    await message.answer(
        NO_ARGS.format(
            **await get_command_args(
                command,
                i18n,
                messages=messages)
        )
    )


@router.message(CustomCommandFilter(commands=['history', 'короче'], ignore_case=True))
@flags.throttling('gen')
@flags.data('messages')
@flags.chat_action("typing")
async def history_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        yalm: balaboba.Yalm,
        messages: list | None = None,
):
    """tell a story, рассказать историю"""

    query = command.args or choice([message.split() for message in messages if messages] + [_("history")])

    if choice(['balaboba', 'markov']) == 'balaboba':
        answer = await yalm.gen(i18n.current_locale, query, 6)
    else:
        query = (_("In short, ")) + query
        answer = markov.gen(i18n.current_locale, messages, query, state_size=2, tries=150000, min_words=50)

    await message.answer(answer)


@router.message(CustomCommandFilter(commands=['future', 'погадай'], ignore_case=True, magic=F.args))
@flags.chat_action("typing")
async def future_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        yalm: balaboba.Yalm,
):
    """predict the future, предсказать будущее"""

    await message.answer(await yalm.gen(i18n.current_locale, command.args, 10))


@router.message(CustomCommandFilter(commands=['future', 'погадай'], ignore_case=True))
@flags.data('messages')
@flags.chat_action("typing")
async def future_no_args_handler(
        message: types.Message,
        command: filters.CommandObject,
        i18n: I18n,
        messages: list | None = None):
    message = await message.answer(_("<b>On coffee grounds?</b>"))
    await message.answer(
        NO_ARGS.format(
            **await get_command_args(
                command,
                i18n,
                messages=messages)
        )
    )
