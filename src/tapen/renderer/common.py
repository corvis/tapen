import abc
from typing import Any, Dict

from tapen.common.domain import PrintJob, TapeParams, Template


class TemplateProcessor(abc.ABC):

    def process(self, template: Template, context: Dict[str, Any]) -> str:
        return self.process_string(template.layout_template, template.name, context)

    @abc.abstractmethod
    def process_string(self, template_str: str, doc_name: str, context: Dict[str, Any]):
        pass


class Renderer(abc.ABC):

    @abc.abstractmethod
    def render(self, print_job: PrintJob, tape_params: TapeParams):
        pass

    @abc.abstractmethod
    def render_bitmap(self, print_job: PrintJob, tape_params: TapeParams, is_preview=False):
        pass


class TemplateRenderingError(Exception):
    def __init__(self, msg: str, original_error: Exception) -> None:
        msg += ": " + str(original_error)
        super().__init__(msg)
        self.original_error = original_error
