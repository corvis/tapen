import ctypes
import enum
from cgitb import reset
from typing import NamedTuple, List

from cli_rack.utils import safe_cast


class TapeInfo(NamedTuple):
    width_mm: int
    width_px: int
    default_margins_mm: float


class DevInfo(object):
    def __init__(self, name: str, vendor_id: int, product_id: int, max_px_buffer=128, dpi=180,
                 unsupported_raster=False, packbits=False, is_plite=False, p700_init=False) -> None:
        self.name = name
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.max_px_buffer = max_px_buffer
        self.dpi = dpi
        self.unsupported_raster = unsupported_raster
        self.packbits = packbits
        self.is_plite = is_plite
        self.p700_init = p700_init


class PTStatusRaw(ctypes.Structure):
    _fields_ = (
        ('printheadmark', ctypes.c_uint8),
        ('size', ctypes.c_uint8),
        ('brother_code', ctypes.c_uint8),
        ('series_code', ctypes.c_uint8),
        ('model', ctypes.c_uint8),
        ('country', ctypes.c_uint8),
        ('reserved_1', ctypes.c_uint16),
        ('error', ctypes.c_uint16),
        ('media_width', ctypes.c_uint8),
        ('media_type', ctypes.c_uint8),
        ('ncol', ctypes.c_uint8),
        ('fonts', ctypes.c_uint8),
        ('jp_fonts', ctypes.c_uint8),
        ('mode', ctypes.c_uint8),
        ('density', ctypes.c_uint8),
        ('media_len', ctypes.c_uint8),
        ('status_type', ctypes.c_uint8),
        ('phase_type', ctypes.c_uint8),
        ('phase_number', ctypes.c_uint16),
        ('notif_number', ctypes.c_uint8),
        ('exp', ctypes.c_uint8),
        ('tape_color', ctypes.c_uint8),
        ('text_color', ctypes.c_uint8),
        ('hw_setting', ctypes.c_uint32),
    )


class PTStatus(object):

    def __init__(self, raw_status: PTStatusRaw) -> None:
        super().__init__()
        self.raw = raw_status

    @property
    def density(self) -> int:
        return self.raw.density

    @property
    def tape_color(self):
        return TapeColor.get_by_code(int(self.raw.tape_color))

    @property
    def text_color(self) -> 'TapeTextColor':
        return TapeTextColor.get_by_code(int(self.raw.text_color))

    @property
    def tape_width(self) -> int:
        return self.raw.media_width


@enum.unique
class BaseColorEnum(enum.Enum):
    def __new__(cls, *args, **kwargs):
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
        result = next(filter(lambda x: x[1].value == code, cls.__members__.items()), None)
        if result is not None:
            return result
        raise KeyError("Invalid value for enum {}: {}".format(cls.__name__, code))


class TapeTextColor(BaseColorEnum):
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
    def get_by_code(cls, code: int) -> 'TapeTextColor':
        return super().get_by_code(code)        # type: ignore


class TapeColor(BaseColorEnum):
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
    CLEARNING = 0xF0, "Clearning", "transparent"
    STENCIL = 0xF1, "Stencil", "grey"
    INCOMPATIBLE = 0xFF, "Incompatible", "grey"

    @classmethod
    def get_by_code(cls, code: int) -> 'TapeColor':
        return super().get_by_code(code)  # type: ignore


_TAPE_PARAMS_180DPI: List[TapeInfo] = [
    TapeInfo(6, 32, 1.0),
    TapeInfo(9, 52, 1.0),
    TapeInfo(12, 76, 1.0),
    TapeInfo(18, 120, 1.0),
    TapeInfo(24, 128, 1.0),
    TapeInfo(36, 192, 1.0),
]

TAPE_PARAMS = {
    180: _TAPE_PARAMS_180DPI
}

DEFAULT_DPI = 180
