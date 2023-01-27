def hide_except_last(value, num=4):
    """Hide everything but last num letters of the string value.

    Attributes:
        value (str): String to obfuscate
        num (int): How many letters to keep visible
    Returns:
        obfuscated string where first letters are hidden with *

    """
    return '*' * (len(value) - num) + value[-num:]
