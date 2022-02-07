import logging
from pathlib import Path
from typing import Optional, Dict, Any

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
            crv.Any(validate.valid_locator,
                    {crv.Required(const.CONF_NAME): str, crv.Required(const.CONF_URL): validate.valid_locator})
        ),
    )
)

CONFIG_SCHEMA = crv.Schema({
    crv.Required(const.CONF_LIBRARIES, default=[]): LIBRARIES_SCHEMA
})

DEFAULT_CONFIG = {}
DEFAULT_CONFIG_FILE_NAME = 'conf.yaml'


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
    return validated_config


def write_config_file(config: Dict[str, Any], p: Path):
    with open(p, "w") as f:
        yaml.dump(config, f)


def load_config(location_override: Optional[str] = None, allow_create=True) -> Dict[str, Any]:
    if location_override is not None:
        return read_config(Path(location_override), allow_create)
    search_locations = [
        Path(DEFAULT_CONFIG_FILE_NAME),
        Path(app_dirs.user_config_dir) / DEFAULT_CONFIG_FILE_NAME
    ]
    location = search_locations[-1]
    for x in search_locations:
        if x.exists():
            location = x
            break
    read_config(location, allow_create)


app_dirs = AppDirs("tapen")