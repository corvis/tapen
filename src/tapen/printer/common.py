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

import abc
from enum import Enum
from typing import List, Optional

from PIL.Image import Image


class Color:
    def __init__(self, id: int, name: str, css_name: str) -> None:
        self.id = id
        self.name = name
        self.css_name = css_name

    def __str__(self) -> str:
        return self.name


class TapeInfo:
    @property
    @abc.abstractmethod
    def id(self) -> int:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise

    @property
    @abc.abstractmethod
    def width_mm(self) -> float:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def padding_vertical_mm(self) -> float:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def color(self) -> Color:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def text_color(self) -> Color:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def density(self) -> int:
        raise NotImplementedError

    def __str__(self) -> str:
        return "{} {} on {}".format(self.name, self.text_color, self.color)


class PrinterStatus(abc.ABC):
    @property
    @abc.abstractmethod
    def tape_info(self) -> TapeInfo:
        raise NotImplementedError


class TapenPrinter(abc.ABC):
    @abc.abstractmethod
    def init(self):
        raise NotImplementedError

    @abc.abstractmethod
    def print_image(self, image: Image, cut_tape=True):
        raise NotImplementedError

    @abc.abstractmethod
    def get_status(self) -> PrinterStatus:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def verbose_name(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def id(self) -> str:
        pass

    def __str__(self) -> str:
        return self.verbose_name


class PrintingMode(Enum):
    HALF_CUT = "half-cut"
    CUT = "cut"


class PrinterFactory(abc.ABC):
    @abc.abstractmethod
    def discover_printers(self) -> List[TapenPrinter]:
        pass

    def get_first_printer(self) -> Optional[TapenPrinter]:
        printers = self.discover_printers()
        return printers[0] if len(printers) > 0 else None

    @abc.abstractmethod
    def get_cached_tape_info(self, printer_id: Optional[str] = None) -> Optional[TapeInfo]:
        pass
