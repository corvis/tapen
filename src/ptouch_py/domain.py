import ctypes
from typing import NamedTuple, List


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
        return self.raw.tape_color

    @property
    def text_color(self):
        return self.raw.text_color

    @property
    def tape_width(self) -> int:
        return self.raw.media_width


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
