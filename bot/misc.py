from pathlib import Path

LOCALE_PATH = Path("core/locales")
LOG_PATH = Path("logs")
MNT_PATH = Path("mnt")


def setup() -> None:
    for path in (LOCALE_PATH, LOG_PATH, MNT_PATH):
        path.mkdir(parents=True, exist_ok=True)
