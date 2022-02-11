from typing import List, Optional

from tapen.printer.brother import PTouchFactory
from tapen.printer.common import PrinterFactory, TapenPrinter, TapeInfo

__DEFAULT_PRINT_FACTORY: Optional['DefaultPrinterFactory'] = None


class DefaultPrinterFactory(PrinterFactory):

    def get_cached_tape_info(self, printer_id: Optional[str] = None) -> TapeInfo:
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
