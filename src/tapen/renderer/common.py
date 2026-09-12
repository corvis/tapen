#
# Tapen - software for managing label printers
# Copyright (C) 2022 Dmitry Berezovsky
#
# Tapen is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tapen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.#

import abc
from typing import Any

from tapen.common.domain import PrintJob, Template
from tapen.printer.common import TapeInfo


class TemplateProcessor(abc.ABC):
    """Interface for rendering template strings with context."""

    def process(self, template: Template, context: dict[str, Any]) -> str:
        """Render a template manifest with context."""
        return self.process_string(template.layout_template, template.name, context)

    @abc.abstractmethod
    def process_string(self, template_str: str, doc_name: str, context: dict[str, Any]):
        """Render a template string with context."""
        raise NotImplementedError


class Renderer(abc.ABC):
    """Interface for rendering print jobs into printable images."""

    def __init__(self) -> None:
        super().__init__()
        self.persist_rendered_image_as_file = False
        self.job_num = 0

    @abc.abstractmethod
    def render(self, print_job: PrintJob, tape_params: TapeInfo):
        """Render a print job into an intermediate representation."""
        raise NotImplementedError

    @abc.abstractmethod
    def render_bitmap(self, print_job: PrintJob, tape_params: TapeInfo, is_preview=False):
        """Render a print job into a monochrome bitmap."""
        raise NotImplementedError


class TemplateRenderingError(Exception):
    """Error raised when template processing fails."""

    def __init__(self, msg: str, original_error: Exception) -> None:
        msg += ": " + str(original_error)
        super().__init__(msg)
        self.original_error = original_error
