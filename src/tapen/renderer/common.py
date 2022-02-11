import abc
from typing import Any, Dict

from tapen.common.domain import PrintJob, Template
from tapen.printer.common import TapeInfo


class TemplateProcessor(abc.ABC):

    def process(self, template: Template, context: Dict[str, Any]) -> str:
        return self.process_string(template.layout_template, template.name, context)

    @abc.abstractmethod
    def process_string(self, template_str: str, doc_name: str, context: Dict[str, Any]):
        pass


class Renderer(abc.ABC):

    def __init__(self) -> None:
        super().__init__()
        self.persist_rendered_image_as_file = False
        self.job_num = 0

    @abc.abstractmethod
    def render(self, print_job: PrintJob, tape_params: TapeInfo):
        pass

    @abc.abstractmethod
    def render_bitmap(self, print_job: PrintJob, tape_params: TapeInfo, is_preview=False):
        pass


class TemplateRenderingError(Exception):
    def __init__(self, msg: str, original_error: Exception) -> None:
        msg += ": " + str(original_error)
        super().__init__(msg)
        self.original_error = original_error
