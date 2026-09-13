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

from abc import ABC, abstractmethod
import logging
import time

from PIL.Image import Image
import usb.core

from ptouch_py import const
from ptouch_py.domain import DevInfo, PTStatus, PTStatusRaw
from ptouch_py.registry import SUPPORTED_DEVICES

LOGGER = logging.getLogger("ptouch_py.core")


class Transport(ABC):
    """Byte transport used by a P-touch printer connection."""

    @abstractmethod
    def write(self, data: bytes) -> None:
        """Write bytes to the printer."""

    @abstractmethod
    def read(self, size: int) -> bytes:
        """Read up to size bytes from the printer."""

    @abstractmethod
    def close(self) -> None:
        """Close the transport."""


class Printer:
    """Brother P-touch printer connection over a byte transport."""

    def __init__(self, transport: Transport, dev_info: DevInfo) -> None:
        super().__init__()
        assert transport is not None and dev_info is not None, "Transport and Dev info MUST be set"
        self._transport = transport
        self.info = dev_info
        self.max_read_attempts = 10
        self.__initialized = False

    def close(self) -> None:
        """Close the underlying transport."""
        self._transport.close()

    @property
    def serial_number(self) -> str:
        """Return the printer serial number."""
        raise NotImplementedError

    @property
    def vendor_name(self) -> str:
        """Return the printer manufacturer name."""
        return "Brother"

    @property
    def product_name(self) -> str:
        """Return the printer product name."""
        return self.info.name

    def _pt_send(self, data: bytes):
        if not self.__initialized and data != const.CMD_INIT:
            raise RuntimeError("Device must be initialized before use. Invoke Printer.init() method.")

        self._transport.write(data)

    def init(self) -> None:
        """Initialize the printer for P-touch commands."""
        self._pt_send(const.CMD_INIT)
        self.__initialized = True

    def get_status(self) -> PTStatus:
        """Read and return the current P-touch status."""
        self._pt_send(const.CMD_STATUS_INFO)
        attempt = 0
        self._pt_send(const.CMD_STATUS_INFO)
        time.sleep(0.5)
        while attempt < self.max_read_attempts:
            time.sleep(0.5)
            status_bytes = self._transport.read(const.PTOUCH_STATUS_REPLY_SIZE)
            if len(status_bytes) == const.PTOUCH_STATUS_REPLY_SIZE:
                if status_bytes[0] == 0x80 and status_bytes[1] == 0x20:
                    return PTStatus(PTStatusRaw.from_buffer(status_bytes))
                else:
                    raise ValueError("Invalid PTouch status reply")
            elif len(status_bytes) == 16:
                raise ValueError("Invalid PT status reply. Raw reply: " + str(status_bytes))
            attempt += 1
        raise ValueError("Unable to read PTouch printer status: timeout")

    def print_image(self, image: Image, cut_tape=True):
        """Print a monochrome image and optionally cut the tape."""
        buffer_size = int(self.info.max_px_buffer / 8)
        # Enable pack bits
        if self.info.packbits:
            self._pt_send(const.CMD_ENABLE_PACKBITS)
        # Raster start
        if self.info.p700_init:
            self._pt_send(const.CMD_RASTER_START_P700)
        else:
            self._pt_send(const.CMD_RASTER_START)
        offset = int(self.info.max_px_buffer / 2) - int(image.height / 2)
        for x in range(image.width):
            raster_line = [0] * buffer_size
            for y in range(image.height):
                pixel_is_set = image.getpixel((x, image.height - 1 - y)) == 0
                if pixel_is_set:
                    self.__rasterline_set_pixel(raster_line, offset + y)
            self.__send_raster(bytes(raster_line))
        self._pt_send(const.CMD_EJECT if cut_tape else const.CMD_ADVANCE)

    def __rasterline_set_pixel(self, rasterline: list[int], pixel_offset: int) -> None:
        size = len(rasterline)
        if pixel_offset > size * 8:
            return
        rasterline[(size - 1) - int(pixel_offset / 8)] |= 1 << (pixel_offset % 8)

    def __send_raster(self, data_frame: bytes) -> None:
        preamble = [0x47, len(data_frame) + 1, 0x00, len(data_frame) - 1]
        buffer = bytes(preamble) + data_frame
        self._pt_send(buffer)

    def __str__(self) -> str:
        return f"{self.vendor_name} {self.product_name} (s/n: {self.serial_number})"


def find_usb_printers() -> list[Printer]:
    """Discover supported P-touch printers on USB."""
    from ptouch_py.impl.usb import UsbPrinter

    result: list[Printer] = []
    devs: list[usb.core.Device] = usb.core.find(find_all=True)
    for dev in devs:
        supported_dev = next(
            filter(lambda x: x.vendor_id == dev.idVendor and x.product_id == dev.idProduct, SUPPORTED_DEVICES), None
        )
        if supported_dev is not None:
            printer = UsbPrinter(dev, supported_dev)
            result.append(printer)
    return result


def get_first_usb_printer() -> Printer | None:
    """Return the first discovered P-touch printer, if any."""
    printers = find_usb_printers()
    return printers[0] if len(printers) > 0 else None


def connect_network(host: str, port: int = 9100, timeout: float = 10.0) -> Printer:
    """Connect to a Brother P-touch raw TCP/IP printer.

    PT-P750W uses port 9100 by default and accepts the same raster stream as
    the USB interface. The returned printer must be initialized before use.
    """
    from ptouch_py.impl.network import NetworkPrinter

    dev_info = next((x for x in SUPPORTED_DEVICES if x.name == "PT-P750W"), None)
    if dev_info is None:
        raise RuntimeError("PT-P750W is not registered as a supported device")
    return NetworkPrinter(host, dev_info, port, timeout)
