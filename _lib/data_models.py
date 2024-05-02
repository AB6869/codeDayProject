import re
from decimal import Decimal, InvalidOperation


class Discard(Exception):
    pass


class Fail(Exception):
    pass


def discard_if(func):
    def validator(instance, attribute, value):
        if func(value):
            raise Discard(f"'{attribute.name}' cannot be '{value}'")

    return validator


def fail_if(func):
    def validator(instance, attribute, value):
        if func(value):
            raise Fail(f"'{attribute.name}' cannot be '{value}'")

    return validator


def str_empty(string):
    return string is None or len(string) == 0


REGISTRATION_NUMBER_PATTERN = re.compile("[0-9]{10}")


def invalid_registration_number(string):
    match = REGISTRATION_NUMBER_PATTERN.fullmatch(string)
    return match is None


CUSTOMER_NUMBER_PATTERN = re.compile("[0-9]{5,6}")


def invalid_customer_number(string):
    match = CUSTOMER_NUMBER_PATTERN.fullmatch(string)
    return match is None


def lower(value):
    if isinstance(value, str):
        return value.lower()
    return value


def try_decimal(string):
    if isinstance(string, Decimal):
        return string
    if isinstance(string, float):
        return Decimal(str(string))
    if isinstance(string, int):
        return Decimal(string)
    try:
        return Decimal(clean_number_string(string))
    except (InvalidOperation, TypeError):
        return None


# Find all instances of "." or "," and replace the last one with "." and remove all others.
def clean_number_string(string):
    components = re.split(r"\,|\.", string)
    if len(components) == 1:
        return string
    return f"{''.join(components[:-1])}.{components[-1]}"
