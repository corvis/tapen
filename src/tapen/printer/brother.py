from typing import List

from ptouch_py.core import Printer as PTouch_Printer, find_printers
from ptouch_py.domain import PTStatus, TapeInfo as PTouch_TapeInfo, TAPE_PARAMS, BaseColorEnum, DEFAULT_DPI
from tapen.printer.common import TapenPrinter, PrinterStatus, Color, TapeInfo, PrinterFactory
from PIL.Image import Image


class PTouchTapeInfo(TapeInfo):

    def __init__(self, tape_info: PTouch_TapeInfo, color: Color, text_color: Color, density: int) -> None:
        super().__init__()
        self.__raw = tape_info
        self.__color = color
        self.__text_color = text_color
        self.__density = density

    @property
    def id(self) -> int:
        return self.__raw.tape_id

    @property
    def name(self) -> str:
        return self.__raw.tape_size

    @property
    def width_mm(self) -> float:
        return self.__raw.width_mm

    def padding_vertical_mm(self) -> float:
        return self.__raw.padding_vertical_mm

    @property
    def color(self) -> Color:
        return self.__color

    @property
    def text_color(self) -> Color:
        return self.__text_color

    @property
    def density(self) -> int:
        return self.__density


class PTouchPrinterStatus(PrinterStatus):

    def __pt_color_enum_to_color(self, color_enum: BaseColorEnum) -> Color:
        return Color(color_enum.code, color_enum.color_name, color_enum.css_color)

    def __init__(self, status: PTStatus) -> None:
        super().__init__()
        self.__raw = status
        self.__tape_color = status.tape_color
        try:
            tape_registry = TAPE_PARAMS[DEFAULT_DPI]
            tape_info = next(filter(lambda x: x.designated_size == status.tape_width, tape_registry), None)
            if tape_info is None:
                raise ValueError("Unsupported tape size {}mm".format(status.tape_width))
        except KeyError:
            raise ValueError("Density {} is not supported")
        tape_color = self.__pt_color_enum_to_color(status.tape_color)
        text_color = self.__pt_color_enum_to_color(status.text_color)
        self.__tape_info = PTouchTapeInfo(tape_info, tape_color, text_color, density=status.density)

    @property
    def tape_info(self) -> TapeInfo:
        return self.__tape_info


class PTouchPrinter(TapenPrinter):

    def __init__(self, ptouch_printer: PTouch_Printer) -> None:
        super().__init__()
        self._ptouch_printer = ptouch_printer

    def init(self):
        self._ptouch_printer.init()

    def print_image(self, image: Image):
        self._ptouch_printer.print_image(image)

    def get_status(self) -> PTouchPrinterStatus:
        return PTouchPrinterStatus(self._ptouch_printer.get_status())

    @property
    def verbose_name(self):
        return str(self._ptouch_printer)


class PTouchFactory(PrinterFactory):

    def discover_printers(self) -> List[TapenPrinter]:
        return [PTouchPrinter(x) for x in find_printers()]
