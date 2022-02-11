#    Tapen - software for managing label printers
#    Copyright (C) 2022 Dmitry Berezovsky
#
#    Tapen is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Tapen is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from typing import Dict, Callable, Any

from cli_rack_validation import crv
from string import ascii_letters, digits

from tapen import const

RESERVED_IDS = ("tapen", "std")

COMBINE_OPERATOR = "&"
VALID_LOCATOR_REGEX = re.compile(r"^[a-zA-Z_0-9\-]+:(.*)$")
VALID_PARAM_NAME_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*([a-zA-Z_][a-zA-Z0-9_]*)*$")


def valid_param_name(value):
    """
    Validate that given value is a valid parameter name. It could include latin letters,
    numbers and symbol _. It also can't start with number
    """
    value = crv.string_strict(value)
    if not VALID_PARAM_NAME_REGEX.fullmatch(value):
        raise crv.Invalid(
            'Invalid name "{}". Name should consist of latin letters, '
            "numbers symbol _ and can't start with digit".format(value)
        )
    return value


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


class _ObjectValidators:
    def __init__(self) -> None:
        super().__init__()
        self.__cache_initialized = False
        self.__cache: Dict[str, Any] = {}

    def build_cache(self):
        for x in dir(crv):
            if x.startswith("_") or x.isupper():
                continue
            self.__cache[x] = getattr(crv, x)
        self.__cache["int"] = self.__cache["int_"]
        self.__cache["float"] = self.__cache["float_"]
        self.__cache["string"] = self.__cache["string"]
        self.__cache["object"] = object
        self.__cache["object_list"] = object_list

    @property
    def validators(self):
        if not self.__cache_initialized:
            self.build_cache()
        return self.__cache

    def validator_by_name(self, name: str) -> Any:
        return self.validators[name]

    def validator_exists(self, name: str) -> bool:
        return name in self.validators

    def validator_def_to_fn(self, validator_def_dict: dict) -> Callable[[Any], Any]:
        funct = self.validators[validator_def_dict[const.CONF_NAME]]
        args = validator_def_dict.get(const.C_ARGS)
        if args is not None:
            if isinstance(args, dict):
                funct = funct(**args)
            elif isinstance(args, list):
                funct = funct(*args)
        return funct

    def create_schema_for_param_def(self, param_def_dict: Dict[str, Dict]) -> crv.Schema:
        res = {}
        for name, cfg in param_def_dict.items():
            default = cfg.get(const.C_DEFAULT, crv.UNDEFINED)
            if cfg.get(const.C_REQUIRED, True):
                name = crv.Required(name, default=default, description=cfg.get(const.C_DESCRIPTION))
            else:
                name = crv.Optional(name, default=default, description=cfg.get(const.C_DESCRIPTION))
            validator_fn = cfg.get(const.C_VALIDATOR, crv.anything)
            res[name] = validator_fn
        return crv.Schema(res)


ObjectValidators = _ObjectValidators()


def valid_validator_name(value):
    value = crv.string_strict(value)
    if ObjectValidators.validator_exists(value):
        return value
    raise crv.Invalid(
        "Invalid validator name '{}'. Valid options are: {}".format(value, ", ".join(ObjectValidators.validators))
    )


validator_def = crv.Schema(
    {
        crv.Required(const.C_NAME): valid_validator_name,
        crv.Optional(const.C_ARGS): crv.Any({valid_param_name: crv.anything}, crv.ensure_list(crv.anything)),
    }
)


def ensure_validator_def(value):
    if isinstance(value, str):
        # If just string - check if it has & operator first
        if COMBINE_OPERATOR in value:
            parts = [x.strip() for x in value.split(COMBINE_OPERATOR)]
            return validator_def({const.CONF_NAME: "combine", const.C_ARGS: parts})
        # Otherwise - just convert to dict
        return validator_def({const.CONF_NAME: value})
    return validator_def(value)


def ensure_valid_validator(value):
    """Normalizes validator definition and converts it into validation function"""
    val_def = ensure_validator_def(value)
    return ObjectValidators.validator_def_to_fn(val_def)


valid_object_def = crv.ensure_schema(
    {
        valid_param_name: {
            crv.Optional(const.C_DESCRIPTION): crv.string_strict,
            crv.Optional(const.C_DEFAULT): crv.anything,
            crv.Optional(const.C_REQUIRED, default=True): crv.boolean,
            crv.Optional(const.C_VALIDATOR): ensure_valid_validator,
        }
    }
)


def object(**kwargs):
    return valid_object_def(kwargs)


def object_list(**kwargs):
    return crv.ensure_list(object(**kwargs))
