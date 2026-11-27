from contract import Editor

from .editor import TextEditor


def create() -> Editor:
    return TextEditor()
