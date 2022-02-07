import re

from cli_rack_validation import crv
from string import ascii_letters, digits

RESERVED_IDS = ("tapen", "std")

VALID_LOCATOR_REGEX = re.compile(r"^[a-zA-Z_0-9\-]+:(.*)$")


def valid_id(value):
    value = crv.string(value)
    if not value:
        raise crv.Invalid("ID must not be empty")
    if value[0].isdigit():
        raise crv.Invalid("First character in ID cannot be a digit.")
    if "-" in value:
        raise crv.Invalid("Dashes are not supported in IDs, please use underscores instead.")
    valid_chars = ascii_letters + digits + "_"
    for char in value:
        if char not in valid_chars:
            raise crv.Invalid(
                "IDs must only consist of upper/lowercase characters, the underscore"
                "character and numbers. The character '{}' cannot be used"
                "".format(char)
            )
    if value.lower() in RESERVED_IDS:
        raise crv.Invalid(f"ID '{value}' is reserved internally and cannot be used")

    return value


def valid_locator(value):
    value = crv.string_strict(value)
    if not VALID_LOCATOR_REGEX.fullmatch(value):
        raise crv.Invalid(
            'Invalid locator "{}". Locator must include locator prefix separated by colon from the locator body'.format(
                value
            )
        )
    return value
