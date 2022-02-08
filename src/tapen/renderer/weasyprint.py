from io import BytesIO
from pathlib import Path
from typing import Optional

import weasyprint as wp
from PIL import Image

from tapen.common.domain import PrintJob, TapeParams
from .common import Renderer, TemplateProcessor

RESOURCES_DIR = Path(__file__).parent / "resources"

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <div class="label">{content}</div>
</body>
</html>
"""

PAGE_SIZE_CONFIG_TEMPLATE = """
@page tape {{
    margin: 0;
    size: {height} {width}; 
}}
"""

BASELINE_FONT = """
html {{
    font-size: {size}px; 
    line-height: {line_height}px; 
}}
"""


class WeasyprintRenderer(Renderer):

    def __init__(self, template_processor: TemplateProcessor) -> None:
        super().__init__()
        self.template_processor = template_processor

    def __get_resource_path(self, name: str):
        path = RESOURCES_DIR / name
        if path.exists():
            return str(path)
        raise ValueError("Resource {} not found at {}".format(name, path))

    def __page_config_css(self, height_px, width_px: float = None) -> str:
        return PAGE_SIZE_CONFIG_TEMPLATE.format(
            width=str(height_px) + "px",
            height="9000px" if width_px is None else str(width_px) + "px"
        )

    def __page_set_baseline_font(self, height_px: int) -> str:
        TAPE_VERTICAL_PADDING = 5
        return BASELINE_FONT.format(
            size=height_px + 2 * TAPE_VERTICAL_PADDING,
            line_height=height_px + 2 * TAPE_VERTICAL_PADDING
        )

    def __find_body_width(self, page: wp.Page) -> Optional[float]:
        try:
            body = page._page_box.all_children()[0].all_children()[0]
            return int(body.width + body.padding_left + body.padding_right)
        except:
            return None

    def __create_processing_context(self, print_job: PrintJob, tape_params: TapeParams, is_preview=False):
        return dict(
            params=print_job.params,
            param=print_job.params,
            tape=tape_params,
            is_preview=is_preview
        )

    def render(self, print_job: PrintJob, tape_params: TapeParams, is_preview=False):
        processing_context = self.__create_processing_context(print_job, tape_params, is_preview)
        label_html = self.template_processor.process(print_job.template, processing_context)

        html = wp.HTML(
            string=BASE_TEMPLATE.format(content=label_html),
            media_type="screen" if is_preview else "print")
        # Page Size config
        HEIGHT_PX = 32
        page_config = self.__page_config_css(HEIGHT_PX)
        auto_width_mode = True
        stylesheets = [
            wp.CSS(filename=self.__get_resource_path("default.css")),
            wp.CSS(string=self.__page_set_baseline_font(HEIGHT_PX))
        ]
        if print_job.template.layout_css is not None:
            label_css = self.template_processor.process_string(print_job.template.layout_css,
                                                               print_job.template.name + "/css", processing_context)
            stylesheets.append(wp.CSS(string=label_css))
        if auto_width_mode:
            rendered_label = html.render(stylesheets=stylesheets + [wp.CSS(string=page_config)])
            calculated_width_px = self.__find_body_width(rendered_label.pages[0])
            page_config = self.__page_config_css(HEIGHT_PX, calculated_width_px)
        rendered_label = html.render(stylesheets=stylesheets + [wp.CSS(string=page_config)])
        # rendered_label.write_png("out.png")
        result_png = BytesIO()
        rendered_label.write_png(result_png)
        result_png.flush()
        result_png.seek(0)
        with open("out.png", "wb") as f:
            f.write(result_png.read())
        return result_png

    def render_bitmap(self, print_job: PrintJob, tape_params: TapeParams, is_preview=False):
        png = self.render(print_job, tape_params, is_preview)
        return Image.open(png, "r", ("png",)).convert("1", dither=3)
        # return Image.open("out.png", "r", ("png",)).convert("1", dither=3)
