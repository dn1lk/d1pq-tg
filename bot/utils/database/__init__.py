import ydb
from aiogram import Dispatcher

import config

from .models import *


async def setup(dispatcher: Dispatcher) -> None:
    driver = ydb.aio.Driver(
        endpoint=config.YDB_ENDPOINT,
        database=config.YDB_DATABASE,
        credentials=ydb.iam.ServiceAccountCredentials.from_file(
            config.YC_SERVICE_ACCOUNT_FILE_CREDENTIALS,
        ),
    )

    await driver.wait(fail_fast=True)

    Model.__pool__ = ydb.aio.SessionPool(driver, size=10)

    # directory: ydb.Directory = await driver.scheme_client.list_directory(config.YDB_DATABASE)
    # children_names = [children.name for children in directory.children]

    # for model in (MainSettings, GenSettings, GPTSettings):
    #     if model.__tablename__ not in children_names:
    #         await model.setup()

    dispatcher.shutdown.register(Model.__pool__.stop)
    dispatcher.shutdown.register(driver.stop)
