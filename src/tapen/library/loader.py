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
import os
from typing import Optional, Dict, Union, Callable

from cli_rack.loader import BaseLoader, BaseLocatorDef, LoaderRegistry, LoadedDataMeta, LoaderError


class LibraryLocatorDef(BaseLocatorDef):
    PREFIX = ""
    TYPE = "lib"
    PATH_SEPARATOR = ":"

    def __init__(
        self, repo_name: str, path: str, name: Optional[str] = None, original_locator: Optional[str] = None
    ) -> None:
        self.repo_name = repo_name
        self.path = path
        self.name = name if name is not None else self.__generate_name()
        super().__init__(name, original_locator)

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update(dict(repo_name=self.repo_name, path=self.path, name=self.name))
        return result

    @classmethod
    def from_dict(cls, locator_dict: dict):
        return cls(
            locator_dict["repo_name"], locator_dict["path"], locator_dict["name"], locator_dict.get("original_locator")
        )

    def __generate_name(self):
        return "-".join((self.repo_name, self.generate_hash_suffix(self.path)))


class LibraryLoader(BaseLoader):
    LOCATOR_CLS = LibraryLocatorDef

    def __init__(
        self, repos: Dict[str, LoadedDataMeta], package_loader: LoaderRegistry, target_dir="tmp/external"
    ) -> None:
        super().__init__(logging.getLogger("loader.lib"), target_dir)
        self.libraries = repos
        self.package_loader = package_loader
        self.reload_interval = None  # Disable cache

    @classmethod
    def locator_to_locator_def(cls, locator_str: Union[str, BaseLocatorDef]) -> LibraryLocatorDef:
        if isinstance(locator_str, str):
            # Parse locator
            locator_components = locator_str.split(cls.LOCATOR_CLS.PATH_SEPARATOR, 1)
            if len(locator_components) != 2:
                raise ValueError("Repository locator should be in form repo://repo-name/path/to/file-or-dir")
            repo_name, path = locator_components[0], locator_components[1]
            return LibraryLocatorDef(repo_name, path, original_locator=locator_str)
        elif isinstance(locator_str, LibraryLocatorDef):
            return locator_str
        else:
            raise ValueError(
                "Locator should be either locator string or LibraryLocatorDef got {}".format(
                    locator_str.__class__.__name__
                )
            )

    @classmethod
    def can_handle(cls, locator: Union[str, BaseLocatorDef]) -> bool:
        if isinstance(locator, str):
            return True
        elif isinstance(locator, BaseLocatorDef):
            return cls.LOCATOR_CLS == locator.__class__
        else:
            raise ValueError(
                "Locator must be either string or subclass of BaseLocatorDef, but {} given".format(
                    locator.__class__.__name__
                )
            )

    def load(
        self,
        locator_: Union[str, BaseLocatorDef],
        target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None,
        force_reload=False,
    ) -> LoadedDataMeta:
        self._logger.info("Loading " + str(locator_))
        locator = self.locator_to_locator_def(locator_)
        if locator.repo_name not in self.libraries:
            raise LoaderError("Unable to load {}. Unknown library {}".format(str(locator_), locator.repo_name))
        lib_meta = self.libraries[locator.repo_name]
        meta = LoadedDataMeta.from_dict(
            lib_meta.to_dict(), os.path.join(lib_meta.path, lib_meta.target_path), self.package_loader
        )
        meta.target_path = locator.path
        full_path = os.path.join(meta.path, meta.target_path)
        if not os.path.exists(full_path):
            other_files = os.listdir(os.path.dirname(full_path))
            alternatives_str = ("\n\tPossible options: " + ", ".join(other_files)) if len(other_files) > 0 else ""
            raise LoaderError(
                "Invalid path within repository {}. {} doesn't exist.".format(lib_meta.locator, locator.path)
                + alternatives_str
            )
        meta.is_file = os.path.isfile(full_path)
        return meta
