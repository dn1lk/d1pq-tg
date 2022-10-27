from aiogram import Router, F

router = Router(name='transitions:private')


@router.message(F.new_chat_members | F.left_chat_member)
async def join_leave_message_pass_handler(_):
    pass
