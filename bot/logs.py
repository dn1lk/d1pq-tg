import logging

from pythonjsonlogger import jsonlogger

import config


class YcLoggingFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["logger"] = record.name

        match record.levelname:
            case "WARNING":
                log_record["level"] = "WARN"
            case "CRITICAL":
                log_record["level"] = "FATAL"
            case _:
                log_record["level"] = record.levelname


def setup() -> None:
    # Base logging
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(YcLoggingFormatter("%(level)s %(logger)s %(message)s"))

    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO, handlers=[stream_handler])

    if config.LOG_TO_FILE:
        for logger_name in (
            "bot",
            "bot.tasks",
            "bot.gpt",
            "bot.uno",
        ):
            file_handler = logging.FileHandler(f"{config.LOG_PATH}/{logger_name}.log")
            file_handler.setFormatter(logging.Formatter("%(asctime)s: %(levelname)s - %(name)s - %(message)s"))

            logger = logging.getLogger(logger_name)
            logger.addHandler(file_handler)
