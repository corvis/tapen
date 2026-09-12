#
# Tapen - software for managing label printers
# Copyright (C) 2022 Dmitry Berezovsky
#
# Tapen is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tapen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from collections.abc import Callable
import logging
import os

from cli_rack.loader import BaseLoader, BaseLocatorDef, LoadedDataMeta, LoaderError, LoaderRegistry


class LibraryLocatorDef(BaseLocatorDef):
    """Locator definition for templates inside a named library."""

    PREFIX = ""
    TYPE = "lib"
    PATH_SEPARATOR = ":"

    def __init__(self, repo_name: str, path: str, name: str | None = None, original_locator: str | None = None) -> None:
        self.repo_name = repo_name
        self.path = path
        self.name = name if name is not None else self.__generate_name()
        super().__init__(name, original_locator)

    def to_dict(self) -> dict:
        """Serialize the locator definition to a dictionary."""
        result = super().to_dict()
        result.update({"repo_name": self.repo_name, "path": self.path, "name": self.name})
        return result

    @classmethod
    def from_dict(cls, locator_dict: dict):
        """Create a locator definition from a dictionary."""
        return cls(
            locator_dict["repo_name"], locator_dict["path"], locator_dict["name"], locator_dict.get("original_locator")
        )

    def __generate_name(self):
        return "-".join((self.repo_name, self.generate_hash_suffix(self.path)))


class LibraryLoader(BaseLoader):
    """Loader that resolves templates from previously loaded libraries."""

    LOCATOR_CLS = LibraryLocatorDef

    def __init__(
        self, repos: dict[str, LoadedDataMeta], package_loader: LoaderRegistry, target_dir="tmp/external"
    ) -> None:
        super().__init__(logging.getLogger("loader.lib"), target_dir)
        self.libraries = repos
        self.package_loader = package_loader
        self.reload_interval = None  # Disable cache

    @classmethod
    def locator_to_locator_def(cls, locator_str: str | BaseLocatorDef) -> LibraryLocatorDef:
        """Convert a locator string or object into a library locator."""
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
            raise TypeError(
                f"Locator should be either locator string or LibraryLocatorDef got {locator_str.__class__.__name__}"
            )

    @classmethod
    def can_handle(cls, locator: str | BaseLocatorDef) -> bool:
        """Return whether this loader can handle a locator."""
        if isinstance(locator, str):
            return True
        elif isinstance(locator, BaseLocatorDef):
            return cls.LOCATOR_CLS == locator.__class__
        else:
            raise TypeError(
                f"Locator must be either string or subclass of BaseLocatorDef, but {locator.__class__.__name__} given"
            )

    def load(
        self,
        locator_: str | BaseLocatorDef,
        target_path_resolver: Callable[[LoadedDataMeta], str] | None = None,
        force_reload=False,
    ) -> LoadedDataMeta:
        """Load metadata for a template path inside a library."""
        self._logger.info("Loading " + str(locator_))
        locator = self.locator_to_locator_def(locator_)
        if locator.repo_name not in self.libraries:
            raise LoaderError(f"Unable to load {locator_!s}. Unknown library {locator.repo_name}")
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
                f"Invalid path within repository {lib_meta.locator}. {locator.path} doesn't exist." + alternatives_str
            )
        meta.is_file = os.path.isfile(full_path)
        return meta
