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
import time
from typing import List, Optional
import usb.core
from PIL.Image import Image

from ptouch_py import const
from ptouch_py.domain import DevInfo, PTStatusRaw, PTStatus
from ptouch_py.registry import SUPPORTED_DEVICES

LOGGER = logging.getLogger("ptouch_py.core")


class Printer(object):
    def __init__(self, usb_dev: usb.core.Device, dev_info: DevInfo) -> None:
        super().__init__()
        assert usb_dev is not None and dev_info is not None, "USB Dev and Dev info MUST be set"
        self.usb_dev = usb_dev
        self.info = dev_info
        self.max_read_attempts = 10
        self.__initialized = False

    @property
    def serial_number(self) -> str:
        return self.usb_dev.serial_number

    @property
    def vendor_name(self) -> str:
        return self.usb_dev.manufacturer

    @property
    def product_name(self) -> str:
        return self.usb_dev.product

    def _pt_send(self, data: bytes):
        if not self.__initialized and data != const.CMD_INIT:
            raise RuntimeError("Device must be initialized before use. Invoke Printer.init() method.")

        msg_len = len(data)
        assert self.usb_dev.write(0x02, data) == msg_len

    def init(self):
        if self.usb_dev.is_kernel_driver_active(0):
            self.usb_dev.detach_kernel_driver(0)
        self.usb_dev.set_configuration()
        cfg = self.usb_dev.get_active_configuration()
        intf = cfg[(0, 0)]
        endpoint: usb.core.Endpoint = usb.util.find_descriptor(
            intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        assert endpoint is not None and endpoint.bEndpointAddress == const.PTOUCH_ENDPOINT
        self._pt_send(const.CMD_INIT)
        self.__initialized = True

    def get_status(self) -> PTStatus:
        self._pt_send(const.CMD_STATUS_INFO)
        attempt = 0
        self._pt_send(const.CMD_STATUS_INFO)
        time.sleep(0.5)
        while attempt < self.max_read_attempts:
            time.sleep(0.5)
            status_bytes = self.usb_dev.read(const.PTOUCH_INPUT_ENDPOINT, const.PTOUCH_STATUS_REPLY_SIZE)
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

    def __rasterline_set_pixel(self, rasterline: List[int], pixel_offset: int) -> None:
        size = len(rasterline)
        if pixel_offset > size * 8:
            return
        rasterline[(size - 1) - int(pixel_offset / 8)] |= 1 << (pixel_offset % 8)

    def __send_raster(self, data_frame: bytes) -> None:
        preamble = [0x47, len(data_frame) + 1, 0x00, len(data_frame) - 1]
        buffer = bytes(preamble) + data_frame
        self._pt_send(buffer)

    def __str__(self) -> str:
        return "{} {} (s/n: {}) [USB dev {} / Bus {}]".format(
            self.vendor_name, self.product_name, self.serial_number, self.usb_dev.address, self.usb_dev.bus
        )


def find_printers() -> List[Printer]:
    result: List[Printer] = []
    devs: List[usb.core.Device] = usb.core.find(find_all=True)
    for dev in devs:
        supported_dev = next(
            filter(lambda x: x.vendor_id == dev.idVendor and x.product_id == dev.idProduct, SUPPORTED_DEVICES), None
        )
        if supported_dev is not None:
            printer = Printer(dev, supported_dev)
            result.append(printer)
    return result


def get_first_printer() -> Optional[Printer]:
    printers = find_printers()
    return printers[0] if len(printers) > 0 else None
