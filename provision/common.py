from functools import partial

from termcolor import colored

success = partial(colored, color='green')
warn = partial(colored, color='yellow')
error = partial(colored, color='red')


def message(text):
    """Format message.

    Args:
        text (str): textual message to format

    """
    text_split = text.split('\n')
    max_text_length = len(max(text_split, key=len))
    length = max_text_length if max_text_length > 76 else 76

    msg = "\n"
    msg += "o" * (length + 4) + "\n"
    line_template = "o {:" + str(length) + "s} o\n"
    for text_part in text_split:
        msg += line_template.format(text_part)
    msg += "o" * (length + 4) + "\n"
    return msg


def print_success(msg):
    return print(success(message(msg)))


def print_warn(msg):
    return print(warn(message(msg)))


def print_error(msg):
    return print(error(message(msg)))
