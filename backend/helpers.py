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