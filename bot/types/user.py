from aiogram.types import User
from aiogram.utils import markdown


def mention_html(self: User, name: str = None):
    return markdown.hlink(name or self.first_name, self.url)


def setup():
    User.mention_html = mention_html
