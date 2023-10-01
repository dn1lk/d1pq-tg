import logging

from pythonjsonlogger import jsonlogger

import config
import misc


class YcLoggingFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['logger'] = record.name
        log_record['level'] = str.replace(str.replace(record.levelname, "WARNING", "WARN"), "CRITICAL", "FATAL")


def setup_logger(logger_name: str):
    logger = logging.getLogger(logger_name)

    if config.LOG_TO_FILE:
        file_handler = logging.FileHandler(f'{misc.BASE_DIR}/logs/{logger_name}.log')
        file_handler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s - %(name)s - %(message)s"))
        logger.addHandler(file_handler)

    return logger


def setup():
    # Base logging
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(YcLoggingFormatter('%(message)s %(level)s %(logger)s'))

    logging.basicConfig(
        level=logging.DEBUG if config.DEBUG else logging.INFO,
        handlers=[
            stream_handler
        ]
    )

    # Bot logging
    setup_logger('bot')

    # Tasks logging
    setup_logger('tasks')
