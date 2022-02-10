import abc
from typing import List, Optional

from PIL.Image import Image

from ptouch_py.core import find_printers


class Color:

    def __init__(self, id: int, name: str, css_name: str) -> None:
        self.id = id
        self.name = name
        self.css_name = css_name

    def __str__(self) -> str:
        return self.name


class TapeInfo:

    @property
    @abc.abstractmethod
    def id(self) -> int:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise

    @property
    @abc.abstractmethod
    def width_mm(self) -> float:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def padding_vertical_mm(self) -> float:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def color(self) -> Color:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def text_color(self) -> Color:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def density(self) -> int:
        raise NotImplementedError

    def __str__(self) -> str:
        return "{} {} on {}".format(self.name, self.text_color, self.color)


class PrinterStatus(abc.ABC):

    @property
    @abc.abstractmethod
    def tape_info(self) -> TapeInfo:
        raise NotImplementedError


class TapenPrinter(abc.ABC):

    @abc.abstractmethod
    def init(self):
        raise NotImplementedError

    @abc.abstractmethod
    def print_image(self, image: Image):
        raise NotImplementedError

    @abc.abstractmethod
    def get_status(self) -> PrinterStatus:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def verbose_name(self):
        raise NotImplementedError

    def __str__(self) -> str:
        return self.verbose_name


class PrinterFactory(abc.ABC):

    @abc.abstractmethod
    def discover_printers(self) -> List[TapenPrinter]:
        pass

    def get_first_printer(self) -> Optional[TapenPrinter]:
        printers = self.discover_printers()
        return printers[0] if len(printers) > 0 else None
