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

import datetime
import os
from pathlib import Path
from typing import Any, Dict, List

from cli_rack.loader import DefaultLoaderRegistry, LoadedDataMeta, InvalidPackageStructure, LoaderRegistry
from cli_rack.utils import ensure_dir

from tapen import config, const, validate
from tapen.common.domain import Template
from tapen.library.loader import LibraryLoader
from tapen.utils import yaml_file_to_dict
from cli_rack_validation import crv

MANIFEST_FILE_NAME = "manifest.yaml"
STANDARD_LIB_NAME = "std"
STANDARD_LIB_PATH = Path(__file__).parent.parent / "resources" / "std-lib"

MANIFEST_META_SCHEMA = crv.Schema(
    {
        crv.Optional(const.MF_NAME): crv.string,
        crv.Optional(const.MF_DESCRIPTION): crv.string,
        crv.Optional(const.MF_AUTHOR): crv.ensure_email_dict,
        crv.Optional(const.MF_LICENSE): crv.string,
    }
)

MANIFEST_LAYOUT_SCHEMA = crv.Schema(
    {
        crv.Required(const.MF_TEMPLATE): crv.string_strict,
        crv.Optional(const.MF_CSS): crv.string,
    }
)

MANIFEST_SCHEMA = crv.Schema(
    {
        crv.Required(const.MF_META_SECTION, default={}): MANIFEST_META_SCHEMA,
        crv.Required(const.MF_PARAMS, default={}): validate.valid_object_def,
        crv.Required(const.MF_LAYOUT): MANIFEST_LAYOUT_SCHEMA,
    }
)


class TemplateLibrary(object):
    def __init__(self, library_config: Dict[str, Any], always_reload_local_libs=False) -> None:
        self.__lib_config: Dict[str, Any] = library_config
        self.lib_loader = DefaultLoaderRegistry.clone()
        self.lib_loader.target_dir = Path(config.app_dirs.user_data_dir) / "lib-cache"
        self.lib_root_dirs: List[str] = [""]
        local_loader = self.lib_loader.get_for_locator("local:nothing")
        if always_reload_local_libs and local_loader:
            local_loader.reload_interval = datetime.timedelta(seconds=0)  # force reload for local repo
        self.loader = DefaultLoaderRegistry.clone()
        self.loader.target_dir = Path(config.app_dirs.user_data_dir) / "lib-cache"
        ensure_dir(str(self.loader.target_dir))
        self.libraries: Dict[str, LoadedDataMeta] = {}
        self.loader.register(LibraryLoader(self.libraries, self.loader, target_dir=self.loader.target_dir))

    def _lib_dir_resolver(self, meta: LoadedDataMeta) -> str:
        for x in self.lib_root_dirs:
            if (Path(meta.path) / x).is_dir():
                return x
        raise InvalidPackageStructure(
            meta, "On of the following folders must be present in repo root: " + str(self.lib_root_dirs)
        )

    def fetch_libraries(self):
        self.libraries.clear()
        self.add_library(STANDARD_LIB_NAME, "local:" + str(STANDARD_LIB_PATH))
        for name, url in self.__lib_config.items():
            self.add_library(name, url)

    def add_library(self, name: str, url: str, force_reload=False):
        if name not in self.__lib_config:
            self.__lib_config[name] = url
        if name not in self.libraries or force_reload:
            self.libraries[name] = self.lib_loader.load(url, self._lib_dir_resolver)

    def load_template(self, locator: str) -> Template:
        meta = self.loader.load(locator)
        template_dir = Path(meta.path) / meta.target_path
        manifest_file = template_dir / MANIFEST_FILE_NAME
        if not manifest_file.is_file():
            raise ValueError(
                "Missing manifest file for template {}. Check your template library and ensure it has valid structure."
                "\n\tCache location: {}".format(locator, meta.path)
            )
        manifest_dict = yaml_file_to_dict(manifest_file)
        manifest_dict = MANIFEST_SCHEMA(manifest_dict)
        return Template(meta.target_path, manifest_dict)
