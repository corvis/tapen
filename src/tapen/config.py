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

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import yaml
from appdirs import AppDirs
from cli_rack.utils import ensure_dir
from cli_rack_validation import crv

from tapen import validate, const

LOGGER = logging.getLogger("config")

LIBRARIES_SCHEMA = crv.Schema(
    crv.Any(
        {validate.valid_id: validate.valid_locator},
        crv.ensure_list(
            crv.Any(
                validate.valid_locator,
                {crv.Required(const.CONF_NAME): str, crv.Required(const.CONF_URL): validate.valid_locator},
            )
        ),
    )
)

CONFIG_SCHEMA = crv.Schema({crv.Required(const.CONF_LIBRARIES, default=[]): LIBRARIES_SCHEMA})

DEFAULT_CONFIG: Dict[str, Any] = {}
DEFAULT_CONFIG_FILE_NAME = "conf.yaml"


def read_config(p: Path, allow_create=True) -> Dict[str, Any]:
    if not p.is_file():
        if allow_create:
            LOGGER.info("Config file doesn't exist. Generating new config...")
            validated_config = CONFIG_SCHEMA(DEFAULT_CONFIG)
            ensure_dir(str(p.parent))
            write_config_file(validated_config, p)
            LOGGER.info("\tPersisted at: {}".format(p))
        else:
            raise ValueError("Config file doesn't exists: " + str(p.absolute()))
    else:
        with open(p, "r") as f:
            yaml_dict = yaml.load(f, Loader=yaml.FullLoader)
        validated_config = CONFIG_SCHEMA(yaml_dict)
    return __normalize_config(validated_config)


def __normalize_config(conf: Dict[str, Any]) -> Dict[str, Any]:
    # Libraries: Standardize representation (convert to dict form)
    libraries = conf.get(const.CONF_LIBRARIES)
    if isinstance(libraries, list):
        mapped = {}
        for x in libraries:
            if isinstance(x, str):
                mapped[x] = x
            else:
                mapped[x[const.CONF_NAME]] = x[const.CONF_URL]
        conf[const.CONF_LIBRARIES] = mapped
    return conf


def write_config_file(config: Dict[str, Any], p: Path):
    with open(p, "w") as f:
        yaml.dump(config, f)


def load_config(location_override: Optional[str] = None, allow_create=True) -> Tuple[str, Dict[str, Any]]:
    if location_override is not None:
        return location_override, read_config(Path(location_override), allow_create)
    search_locations = [Path(DEFAULT_CONFIG_FILE_NAME), Path(app_dirs.user_config_dir) / DEFAULT_CONFIG_FILE_NAME]
    location = search_locations[-1]
    for x in search_locations:
        if x.exists():
            location = x
            break
    return str(location), read_config(location, allow_create)


app_dirs = AppDirs("tapen")
