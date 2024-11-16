from aiogram import Bot, types


async def my_is_not_admin_filter(message: types.Message, bot: Bot) -> bool:
    """Filter if bot is not admin"""

    member = await bot.get_chat_member(message.chat.id, bot.id)
    return not (isinstance(member, types.ChatMemberAdministrator) and member.can_manage_chat)
