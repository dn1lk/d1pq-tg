from utils import database


async def clear_data(
    main_settings: database.MainSettings,
    gen_settings: database.GenSettings,
    gpt_settings: database.GPTSettings,
) -> None:
    await main_settings.delete()
    await gen_settings.delete()
    await gpt_settings.delete()
