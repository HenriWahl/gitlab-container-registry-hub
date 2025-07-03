import logging
from os import _exit


c

def plural_or_not(count: int, word: str) -> str:
    """
    decide if a word has to be in plural because its appears as multiple
    :param count:
    :param string:
    :return:
    """
    if count > 1:
        return f'{count} {word}s'
    else:
        return f'{count} {word}'


def exit(message='', code=1):
    """
    exit with message and code
    :param message:
    :param code:
    :return:
    """
    print(message)
    _exit(code)


