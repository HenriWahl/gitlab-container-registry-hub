import logging
from os import _exit
from sys import stdout


class Logger():
    def __init__(self, logger_name: str = '', log_level: str = 'INFO'):
        """
        Initialize the logger with a specific name.
        :param logger_name: Name of the logger
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        # needed for logging to stdout
        self.logger.addHandler(logging.StreamHandler(stdout))


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


