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

import pickle
from pathlib import Path
from typing import List, Optional

from cli_rack.utils import ensure_dir

from ptouch_py.core import Printer as PTouch_Printer, find_printers
from ptouch_py.domain import PTStatus, TapeInfo as PTouch_TapeInfo, TAPE_PARAMS, BaseColorEnum, DEFAULT_DPI
from tapen import config
from tapen.printer.common import TapenPrinter, PrinterStatus, Color, TapeInfo, PrinterFactory
from PIL.Image import Image

TAPE_CACHE_DIR = Path(config.app_dirs.user_cache_dir) / "tape-cache"


class PTouchTapeInfo(TapeInfo):
    def __init__(self, tape_info: PTouch_TapeInfo, color: Color, text_color: Color, density: int) -> None:
        super().__init__()
        self.__raw = tape_info
        self.__color = color
        self.__text_color = text_color
        self.__density = density

    @property
    def id(self) -> int:
        return self.__raw.tape_id

    @property
    def name(self) -> str:
        return self.__raw.tape_size

    @property
    def width_mm(self) -> float:
        return self.__raw.width_mm

    @property
    def padding_vertical_mm(self) -> float:
        return self.__raw.padding_vertical_mm

    @property
    def color(self) -> Color:
        return self.__color

    @property
    def text_color(self) -> Color:
        return self.__text_color

    @property
    def density(self) -> int:
        return self.__density


class PTouchPrinterStatus(PrinterStatus):
    def __pt_color_enum_to_color(self, color_enum: BaseColorEnum) -> Color:
        return Color(color_enum.code, color_enum.color_name, color_enum.css_color)

    def __init__(self, status: PTStatus) -> None:
        super().__init__()
        self.__raw = status
        self.__tape_color = status.tape_color
        try:
            tape_registry = TAPE_PARAMS[DEFAULT_DPI]
            tape_info = next(filter(lambda x: x.designated_size == status.tape_width, tape_registry), None)
            if tape_info is None:
                raise ValueError("Unsupported tape size {}mm".format(status.tape_width))
        except KeyError:
            raise ValueError("Density {} is not supported")
        tape_color = self.__pt_color_enum_to_color(status.tape_color)
        text_color = self.__pt_color_enum_to_color(status.text_color)
        self.__tape_info = PTouchTapeInfo(tape_info, tape_color, text_color, density=status.density)

    @property
    def tape_info(self) -> TapeInfo:
        return self.__tape_info


class PTouchPrinter(TapenPrinter):
    def __init__(self, ptouch_printer: PTouch_Printer) -> None:
        super().__init__()
        self._ptouch_printer = ptouch_printer

    def init(self):
        self._ptouch_printer.init()

    def print_image(self, image: Image, cut_tape=True):
        self._ptouch_printer.print_image(image, cut_tape)

    def get_status(self) -> PTouchPrinterStatus:
        status = PTouchPrinterStatus(self._ptouch_printer.get_status())
        self.__persist_tape_info(status.tape_info)
        return status

    @property
    def verbose_name(self):
        return str(self._ptouch_printer)

    @property
    def id(self) -> str:
        return self._ptouch_printer.serial_number

    def __persist_tape_info(self, tape_info: TapeInfo):
        ensure_dir(str(TAPE_CACHE_DIR))
        cache_file = TAPE_CACHE_DIR / (self.id + ".bin")
        with open(cache_file, "wb") as f:
            pickle.dump(tape_info, f)


class PTouchFactory(PrinterFactory):
    def get_cached_tape_info(self, printer_id: Optional[str] = None) -> Optional[TapeInfo]:
        ensure_dir(str(TAPE_CACHE_DIR))
        cache_file: Optional[Path] = None
        if printer_id:
            cache_file = TAPE_CACHE_DIR / (printer_id + ".bin")
        else:
            for x in TAPE_CACHE_DIR.iterdir():
                if x.is_file() and x.name.endswith(".bin"):
                    cache_file = x
                    continue
        if cache_file is None or not cache_file.exists():
            return None
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    def discover_printers(self) -> List[TapenPrinter]:
        return [PTouchPrinter(x) for x in find_printers()]
