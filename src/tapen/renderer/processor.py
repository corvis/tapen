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

from typing import Dict, Any

import jinja2

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
            raise TemplateRenderingError('Error in template "{}": {}'.format(doc_name, str(e)), e) from e
