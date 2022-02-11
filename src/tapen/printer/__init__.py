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

from typing import List, Optional

from tapen.printer.brother import PTouchFactory
from tapen.printer.common import PrinterFactory, TapenPrinter, TapeInfo

__DEFAULT_PRINT_FACTORY: Optional["DefaultPrinterFactory"] = None


class DefaultPrinterFactory(PrinterFactory):
    def get_cached_tape_info(self, printer_id: Optional[str] = None) -> Optional[TapeInfo]:
        return self.__ptouch_fectory.get_cached_tape_info(printer_id)

    def __init__(self) -> None:
        super().__init__()
        self.__ptouch_fectory = PTouchFactory()

    def discover_printers(self) -> List[TapenPrinter]:
        return self.__ptouch_fectory.discover_printers()


def get_print_factory() -> PrinterFactory:
    global __DEFAULT_PRINT_FACTORY
    if __DEFAULT_PRINT_FACTORY is None:
        __DEFAULT_PRINT_FACTORY = DefaultPrinterFactory()
    return __DEFAULT_PRINT_FACTORY
