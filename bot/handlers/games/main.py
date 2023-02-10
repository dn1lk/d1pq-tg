@router.message(CustomCommandFilter('play', 'поиграем', magic=F.args))
async def game_handler(message: types.Message):
    """, сыграть в игру"""

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