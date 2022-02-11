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

from typing import Optional

from .common import Renderer, TemplateProcessor
from .processor import JinjaTemplateProcessor
from .weasyprint import WeasyprintRenderer

__DEFAULT_RENDERER: Optional[Renderer] = None
__DEFAULT_PROCESSOR: Optional[TemplateProcessor] = None


def get_default_template_processor() -> TemplateProcessor:
    global __DEFAULT_PROCESSOR
    if __DEFAULT_PROCESSOR is None:
        __DEFAULT_PROCESSOR = JinjaTemplateProcessor()
    return __DEFAULT_PROCESSOR


def get_default_renderer() -> Renderer:
    global __DEFAULT_RENDERER
    if __DEFAULT_RENDERER is None:
        __DEFAULT_RENDERER = WeasyprintRenderer(get_default_template_processor())
    return __DEFAULT_RENDERER
