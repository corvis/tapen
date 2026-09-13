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

import ctypes
import enum
from typing import NamedTuple


class TapeInfo(NamedTuple):
    """Static metadata for a supported tape size."""

    tape_size: str
    designated_size: int
    tape_id: int
    width_mm: float
    width_px: int
    padding_vertical_mm: float


class DevInfo:
    """Static metadata for a supported P-touch device."""

    def __init__(
        self,
        name: str,
        vendor_id: int,
        product_id: int,
        max_px_buffer=128,
        dpi=180,
        unsupported_raster=False,
        packbits=False,
        is_plite=False,
        p700_init=False,
        support_network=False,
    ) -> None:
        self.name = name
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.max_px_buffer = max_px_buffer
        self.support_network = support_network
        self.dpi = dpi
        self.unsupported_raster = unsupported_raster
        self.packbits = packbits
        self.is_plite = is_plite
        self.p700_init = p700_init


class PTStatusRaw(ctypes.Structure):
    """Raw P-touch status response structure."""

    _fields_ = (
        ("printheadmark", ctypes.c_uint8),
        ("size", ctypes.c_uint8),
        ("brother_code", ctypes.c_uint8),
        ("series_code", ctypes.c_uint8),
        ("model", ctypes.c_uint8),
        ("country", ctypes.c_uint8),
        ("reserved_1", ctypes.c_uint16),
        ("error", ctypes.c_uint16),
        ("media_width", ctypes.c_uint8),
        ("media_type", ctypes.c_uint8),
        ("ncol", ctypes.c_uint8),
        ("fonts", ctypes.c_uint8),
        ("jp_fonts", ctypes.c_uint8),
        ("mode", ctypes.c_uint8),
        ("density", ctypes.c_uint8),
        ("media_len", ctypes.c_uint8),
        ("status_type", ctypes.c_uint8),
        ("phase_type", ctypes.c_uint8),
        ("phase_number", ctypes.c_uint16),
        ("notif_number", ctypes.c_uint8),
        ("exp", ctypes.c_uint8),
        ("tape_color", ctypes.c_uint8),
        ("text_color", ctypes.c_uint8),
        ("hw_setting", ctypes.c_uint32),
    )


class PTStatus:
    """Parsed P-touch printer status."""

    def __init__(self, raw_status: PTStatusRaw) -> None:
        super().__init__()
        self.raw = raw_status

    @property
    def density(self) -> int:
        """Return the reported print density."""
        return self.raw.density

    @property
    def tape_color(self):
        """Return the reported tape color."""
        return TapeColor.get_by_code(int(self.raw.tape_color))

    @property
    def text_color(self) -> "TapeTextColor":
        """Return the reported tape text color."""
        return TapeTextColor.get_by_code(int(self.raw.text_color))

    @property
    def tape_width(self) -> int:
        """Return the reported tape width in millimeters."""
        return self.raw.media_width


@enum.unique
class BaseColorEnum(enum.Enum):
    """Base enum for P-touch color codes."""

    def __new__(cls, *args, **kwargs):
        """Create an enum value from a P-touch color code."""
        value = args[0]
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, code, color_name: str, css_color: str):
        self.code = code
        self.color_name = color_name
        self.css_color = css_color

    @classmethod
    def get_by_code(cls, code: int):
        """Return an enum member by P-touch color code."""
        result = next(filter(lambda x: x[1].value == code, cls.__members__.items()), None)
        if result is not None:
            return result[1]
        raise KeyError(f"Invalid value for enum {cls.__name__}: {code}")


class TapeTextColor(BaseColorEnum):
    """Known P-touch tape text colors."""

    WHITE = 0x01, "White", "white"
    RED = 0x04, "Red", "red"
    BLUE = 0x05, "Blue", "blue"
    BLACK = 0x08, "Black", "black"
    GOLD = 0x0A, "Golden", "yellow"
    BLUE_F = 0x62, "Blue (f)", "blue"
    CLEARNING = 0xF0, "Clearning", "transparent"
    STENCIL = 0xF1, "Stencil", "grey"
    OTHER = 0x02, "Other", "grey"
    INCOMPATIBLE = 0xFF, "Incompatible", "grey"

    @classmethod
    def get_by_code(cls, code: int) -> "TapeTextColor":
        """Return a tape text color by P-touch code."""
        return super().get_by_code(code)  # type: ignore


class TapeColor(BaseColorEnum):
    """Known P-touch tape background colors."""

    WHITE = 0x01, "White", "white"
    OTHER = 0x02, "Other", "gray"
    TRANSPARENT = 0x03, "Transparent", "transparent"
    RED = 0x04, "Red", "red"
    BLUE = 0x05, "Blue", "blue"
    YELLOW = 0x06, "White", "white"
    GREEN = 0x07, "White", "white"
    BLACK = 0x08, "White", "white"
    TRANSPARENT_W_TEXT = 0x01, "Transparent (white text)", "transparent"
    MATTE_WHITE = 0x20, "White (matte)", "white"
    MATTE_TRANSPARENT = 0x21, "Transparent (matte)", "transparent"
    MATTE_SILVER = 0x22, "Silver (matte)", "silver"
    SATIN_GOLD = 0x23, "Golden (satin)", "gold"
    SATIN_SILVER = 0x24, "Silver (satin)", "silver"
    # TODO: extend the list with the rest of items
    BLUE_F = 0x62, "Blue (F)", "blue"
    WHITE_TUBE = 0x70, "White (tube)", "white"
    WHITE_FLEX_ID = 0x90, "White (flex id)", "white"
    YELLOW_FLEX_ID = 0x91, "Yellow (flex id)", "yellow"
    CLEARNING = 0xF0, "Clearning", "transparent"
    STENCIL = 0xF1, "Stencil", "grey"
    INCOMPATIBLE = 0xFF, "Incompatible", "grey"

    @classmethod
    def get_by_code(cls, code: int) -> "TapeColor":
        """Return a tape background color by P-touch code."""
        return super().get_by_code(code)  # type: ignore


_TAPE_PARAMS_180DPI: list[TapeInfo] = [
    TapeInfo("3.5mm", 3, 263, 3.4, 24, 0),
    TapeInfo("6mm", 6, 257, 5.9, 42, 0.7),
    TapeInfo("9mm", 9, 258, 9.0, 64, 0.98),
    TapeInfo("12mm", 12, 259, 11.9, 84, 0.98),
    TapeInfo("18mm", 18, 260, 18.1, 128, 1.12),
    TapeInfo("24mm", 24, 261, 24, 170, 2.96),
]

TAPE_PARAMS: dict[int, list[TapeInfo]] = {180: _TAPE_PARAMS_180DPI}

DEFAULT_DPI = 180
