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
    def __init__(self, template: Template, params: Dict[str, Any], cut_tape=True) -> None:
        self.template = template
        self.params = params
        self.cut_tape = cut_tape
