"""create a schema to validate a password"""

from typing import Dict, List, Tuple

from password_validator import PasswordValidator, lib  # type: ignore[import-untyped]

from common.tools import split_long_string
from settings import DEBUG

PASSWORD_SCHEMA = PasswordValidator()
if not DEBUG:
    PASSWORD_SCHEMA.min(8)
    PASSWORD_SCHEMA.max(100)
    PASSWORD_SCHEMA.has().letters()
    PASSWORD_SCHEMA.has().uppercase()
    PASSWORD_SCHEMA.has().lowercase()
    PASSWORD_SCHEMA.has().digits()
    PASSWORD_SCHEMA.has().symbols()
    PASSWORD_SCHEMA.has().no().spaces()


_SCHEMA_LIB_RULE_MAP = {
    lib.minimum: "min",
    lib.maximum: "max",
    lib.letters: "letter",
    lib.uppercase: "uppercase",
    lib.lowercase: "lowercase",
    lib.digits: "digit",
    lib.spaces: "space",
    lib.symbols: "symbol",
}


RULES: Dict[str, int | bool | None] = {
    "min": None,
    "max": None,
    "letter": None,
    "uppercase": None,
    "lowercase": None,
    "digit": None,
    "space": None,
    "symbol": None,
}


def _extract_message(rules: Dict[str, int | bool | None]) -> Tuple[List[str], List[str]]:
    allowed: List[str] = []
    disallowed: List[str] = []
    for key, value in rules.items():
        if key == "min" and value is not None:
            allowed.append(f"at least {rules['min']} characters")
        elif key == "max" and value is not None:
            allowed.append(f"at most {rules['max']} characters")

        if value is True:
            allowed.append(f"one {key}")
        elif value is False:
            disallowed.append(f"no {key}")

    return allowed, disallowed


def _make_message(message_list: List[str]) -> str:
    if len(message_list) > 1:
        return ", ".join(message_list[:-1]) + " and " + message_list[-1]
    return message_list[0]


def get_schema_rules(schema: PasswordValidator = PASSWORD_SCHEMA) -> str:
    """return the user helper string for the given schema"""

    rules = RULES.copy()

    for prop in schema.properties:
        item = _SCHEMA_LIB_RULE_MAP[prop["method"]]
        if prop["positive"]:
            try:
                rules[item] = prop["arguments"][0]
            except IndexError:
                rules[item] = True
        else:
            rules[item] = False

    allowed, disallowed = _extract_message(rules)

    message = ""
    if allowed:
        message += "The password must contain " + _make_message(allowed) + ". "
    if disallowed:
        if allowed:
            message += "And "
        else:
            message += "In the password "
        message += _make_message(disallowed) + " is allowed."

    return message or "There is no special requirement for password."


def get_password_hint(max_length: int | None = 100) -> str:
    """return the password hint with the given max length for each line"""

    hint = get_schema_rules(PASSWORD_SCHEMA)
    if max_length is None or len(hint) < max_length:
        return hint

    return split_long_string(hint, max_length)
