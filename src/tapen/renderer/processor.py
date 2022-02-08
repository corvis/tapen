from typing import Dict, Any

import jinja2

from tapen.common.domain import Template
from .common import TemplateProcessor, TemplateRenderingError


class JinjaTemplateProcessor(TemplateProcessor):
    def __init__(self) -> None:
        super().__init__()
        self.jinja_environment = jinja2.Environment()

    def process_string(self, template_str: str, doc_name: str, context: Dict[str, Any]):
        jinja_template = self.jinja_environment.from_string(template_str, template_class=jinja2.Template)
        try:
            return jinja_template.render(context)
        except jinja2.TemplateError as e:
            raise TemplateRenderingError('Error in template "{}": '.format(doc_name, str(e)), e) from e
