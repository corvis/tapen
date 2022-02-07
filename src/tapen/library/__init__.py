import os
from pathlib import Path
from typing import Any, Dict, List

from cli_rack.loader import DefaultLoaderRegistry, LoadedDataMeta, InvalidPackageStructure, LoaderRegistry
from cli_rack.utils import ensure_dir

from tapen import config
from tapen.library.loader import LibraryLoader


class TemplateLibrary(object):
    def __init__(self, library_config: Dict[str, Any]) -> None:
        self.__lib_config: Dict[str, Any] = library_config
        self.lib_loader = DefaultLoaderRegistry.clone()
        self.lib_loader.target_dir = Path(config.app_dirs.user_data_dir) / "lib-cache"
        self.lib_root_dirs: List[str] = [""]
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
        for name, url in self.__lib_config.items():
            self.libraries[name] = self.lib_loader.load(url, self._lib_dir_resolver)

    def load(self, locator: str):
        self.loader.load(locator)
