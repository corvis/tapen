from typing import Any, Dict, Optional

from tapen import const


class Template:

    def __init__(self, name: str, _dict: Dict[str, Any]) -> None:
        super().__init__()
        self.raw = _dict
        self.name = name

    def name(self):
        return self.name

    @property
    def layout_template(self) -> str:
        return self.raw[const.MF_LAYOUT][const.MF_TEMPLATE]

    @property
    def layout_css(self) -> Optional[str]:
        return self.raw[const.MF_LAYOUT].get(const.MF_CSS, None)


class PrintJob(object):
    def __init__(self, template: Template, params: Dict[str, Any]) -> None:
        self.template = template
        self.params = params


class TapeParams(object):

    @property
    def tape_width_mm(self) -> float:
        raise NotImplementedError

    @property
    def tape_width_px(self) -> int:
        raise NotImplementedError
