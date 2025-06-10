from utils import database


async def clear_data(
    main_settings: database.models.MainSettings,
    gen_settings: database.models.GenSettings,
    gpt_settings: database.models.GPTSettings,
) -> None:
    await main_settings.delete()
    await gen_settings.delete()
    await gpt_settings.delete()
