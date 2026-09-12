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

import abc
from enum import Enum

from PIL.Image import Image


class Color:
    """Color metadata used by printer and rendering backends."""

    def __init__(self, color_id: int, name: str, css_name: str) -> None:
        self.id = color_id
        self.name = name
        self.css_name = css_name

    def __str__(self) -> str:
        return self.name


class TapeInfo:
    """Information about the loaded printer tape."""

    @property
    @abc.abstractmethod
    def id(self) -> int:
        """Return the tape identifier."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the tape display name."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def width_mm(self) -> float:
        """Return the tape width in millimeters."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def padding_vertical_mm(self) -> float:
        """Return the non-printable vertical padding in millimeters."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def color(self) -> Color:
        """Return the tape background color."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def text_color(self) -> Color:
        """Return the tape text color."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def density(self) -> int:
        """Return the tape density."""
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{self.name} {self.text_color} on {self.color}"


class PrinterStatus(abc.ABC):
    """Status reported by a printer backend."""

    @property
    @abc.abstractmethod
    def tape_info(self) -> TapeInfo:
        """Return the loaded tape information."""
        raise NotImplementedError


class TapenPrinter(abc.ABC):
    """Abstract printer interface used by Tapen."""

    @abc.abstractmethod
    def init(self):
        """Initialize the printer for use."""
        raise NotImplementedError

    @abc.abstractmethod
    def print_image(self, image: Image, cut_tape=True):
        """Print an image and optionally cut the tape."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_status(self) -> PrinterStatus:
        """Return the current printer status."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def verbose_name(self):
        """Return a human-readable printer name."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """Return the printer identifier."""
        raise NotImplementedError

    def __str__(self) -> str:
        return self.verbose_name


class PrintingMode(Enum):
    """Supported tape cutting modes."""

    HALF_CUT = "half-cut"
    CUT = "cut"


class PrinterFactory(abc.ABC):
    """Factory interface for discovering printers."""

    @abc.abstractmethod
    def discover_printers(self) -> list[TapenPrinter]:
        """Return discovered printers."""
        raise NotImplementedError

    def get_first_printer(self) -> TapenPrinter | None:
        """Return the first discovered printer, if any."""
        printers = self.discover_printers()
        return printers[0] if len(printers) > 0 else None

    @abc.abstractmethod
    def get_cached_tape_info(self, printer_id: str | None = None) -> TapeInfo | None:
        """Return cached tape information for a printer."""
        raise NotImplementedError
