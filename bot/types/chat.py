from aiogram import html
from aiogram.types import Chat


def mention_html(self: Chat, title: str = None):
    return html.quote(title or self.title)


def setup():
    Chat.mention_html = mention_html
