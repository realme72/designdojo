from contract import Chat

from .chat import ChatService


def create() -> Chat:
    return ChatService()
