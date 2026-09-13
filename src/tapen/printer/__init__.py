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

from tapen.printer.brother import PTouchFactory
from tapen.printer.common import PrinterFactory, TapeInfo, TapenPrinter

__DEFAULT_PRINT_FACTORY: PrinterFactory | None = None


class DefaultPrinterFactory(PrinterFactory):
    """Default printer factory backed by Brother P-touch discovery."""

    def get_cached_tape_info(self, printer_id: str | None = None) -> TapeInfo | None:
        """Return cached tape information for a Brother printer."""
        return self.__ptouch_fectory.get_cached_tape_info(printer_id)

    def __init__(self, configured_printers: list[dict] | None = None) -> None:
        super().__init__()
        self.__ptouch_fectory = PTouchFactory()
        self.__configured_printers = configured_printers or []

    def discover_printers(self) -> list[TapenPrinter]:
        """Discover available Brother P-touch printers."""
        return self.__ptouch_fectory.discover_printers(self.__configured_printers)

    def discover_usb_printers(self) -> list[TapenPrinter]:
        """Discover currently connected USB Brother P-touch printers."""
        return self.__ptouch_fectory.discover_usb_printers()


def get_print_factory(configured_printers: list[dict] | None = None) -> PrinterFactory:
    """Return the process-wide default printer factory."""
    global __DEFAULT_PRINT_FACTORY
    if __DEFAULT_PRINT_FACTORY is None:
        __DEFAULT_PRINT_FACTORY = DefaultPrinterFactory(configured_printers)
    return __DEFAULT_PRINT_FACTORY
