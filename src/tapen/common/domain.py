from typing import Any, Dict


class Template:
    pass


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
