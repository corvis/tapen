import logging
from io import BytesIO
from pathlib import Path
from typing import Optional

import weasyprint as wp
from PIL import Image
from cli_rack.utils import ensure_dir

from tapen.common.domain import PrintJob, TapeParams
from .common import Renderer, TemplateProcessor
from .. import config

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
    font-size: {size}; 
    line-height: {line_height};
}}
body {{
    padding: {padding_top} {padding_right} {padding_bottom} {padding_left};
}}
"""

LOGGER = logging.getLogger("renderer.weasyprint")


class WeasyprintRenderer(Renderer):

    def __init__(self, template_processor: TemplateProcessor) -> None:
        super().__init__()
        self.template_processor = template_processor
        self.persist_rendered_image_as_file = False


    def __get_resource_path(self, name: str):
        path = RESOURCES_DIR / name
        if path.exists():
            return str(path)
        raise ValueError("Resource {} not found at {}".format(name, path))

    def __generate_temp_file(self, file_name: str) -> Path:
        path = Path(config.app_dirs.user_cache_dir) / "debug"
        ensure_dir(str(path))
        return path / file_name

    def __page_config_css(self, height_px, width_px: float = None) -> str:
        # return PAGE_SIZE_CONFIG_TEMPLATE.format(
        #     width=str(height_px) + "px",
        #     height="9000px" if width_px is None else str(width_px) + "px"
        # )
        return PAGE_SIZE_CONFIG_TEMPLATE.format(
            width="6mm",
            height="9000px" if width_px is None else str(width_px) + "px"
        )

    def __page_set_baseline_font(self, height_px: int) -> str:
        TAPE_VERTICAL_PADDING = 0.70
        TAPE_HORIZONTAL_PADDING = 0
        height_mm = 4.5
        return BASELINE_FONT.format(
            size="{}mm".format(height_mm),
            line_height="{}mm".format(height_mm),
            padding_top="{}mm".format(TAPE_VERTICAL_PADDING),
            padding_bottom="{}mm".format(TAPE_VERTICAL_PADDING),
            padding_left="{}px".format(TAPE_HORIZONTAL_PADDING),
            padding_right="{}px".format(TAPE_HORIZONTAL_PADDING)
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

    def render(self, print_job: PrintJob, tape_params: TapeParams, is_preview=False, dpi=180):
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
        result_png = BytesIO()
        rendered_label.write_png(result_png, resolution=dpi)
        result_png.flush()
        result_png.seek(0)
        if self.persist_rendered_image_as_file:
            path = self.__generate_temp_file("rendered-label.png")
            with open(path, "wb") as f:
                LOGGER.debug("Persisting generated image at {}".format(path))
                f.write(result_png.read())
        return result_png

    def render_bitmap(self, print_job: PrintJob, tape_params: TapeParams, is_preview=False, dpi=180):
        png = self.render(print_job, tape_params, is_preview, dpi)
        bitmap = Image.open(png, "r", ("png",)).convert("1", dither=3)
        if self.persist_rendered_image_as_file:
            path = self.__generate_temp_file("rendered-label.bmp")
            LOGGER.debug("Persisting rendered bitmap at {}".format(path))
            bitmap.save(path)

        return bitmap