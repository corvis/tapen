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
import usb.core
import usb.util

from ptouch_py import const
from ptouch_py.core import Printer, Transport
from ptouch_py.domain import DevInfo


class _USBTransport(Transport):
    def __init__(self, usb_dev: usb.core.Device) -> None:
        self.usb_dev = usb_dev

    def write(self, data: bytes) -> None:
        assert self.usb_dev.write(0x02, data) == len(data)

    def read(self, size: int) -> bytes:
        return bytes(self.usb_dev.read(const.PTOUCH_INPUT_ENDPOINT, size))

    def close(self) -> None:
        pass


class UsbPrinter(Printer):
    """Brother P-touch printer connected over USB."""

    def __init__(self, usb_dev: usb.core.Device, dev_info: DevInfo) -> None:
        super().__init__(_USBTransport(usb_dev), dev_info)
        self.usb_dev = usb_dev

    @property
    def serial_number(self) -> str:
        """Return the USB device serial number."""
        return self.usb_dev.serial_number

    @property
    def vendor_name(self) -> str:
        """Return the USB device manufacturer name."""
        return self.usb_dev.manufacturer

    @property
    def product_name(self) -> str:
        """Return the USB device product name."""
        return self.usb_dev.product

    def init(self) -> None:
        """Initialize the USB device for P-touch commands."""
        if self.usb_dev.is_kernel_driver_active(0):
            self.usb_dev.detach_kernel_driver(0)
        self.usb_dev.set_configuration()
        cfg = self.usb_dev.get_active_configuration()
        intf = cfg[(0, 0)]
        endpoint: usb.core.Endpoint = usb.util.find_descriptor(
            intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        assert endpoint is not None and endpoint.bEndpointAddress == const.PTOUCH_ENDPOINT
        super().init()
