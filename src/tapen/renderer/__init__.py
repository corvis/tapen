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
