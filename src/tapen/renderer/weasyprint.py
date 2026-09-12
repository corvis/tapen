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

from io import BytesIO
import logging
from pathlib import Path

from cli_rack.utils import ensure_dir
from PIL import Image
import pymupdf
import weasyprint as wp

from tapen.common.domain import PrintJob

from .. import config
from ..printer.common import TapeInfo
from .common import Renderer, TemplateProcessor

RESOURCES_DIR = Path(__file__).parent / "resources"

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <div class="label" style="white-space: nowrap;">{content}</div>
</body>
</html>
"""

PAGE_SIZE_CONFIG_TEMPLATE = """
@page {{
    margin: 0;
    padding: 0;
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

DEFAULT_RENDERER_DPI = 96


class WeasyprintRenderer(Renderer):
    """Renderer that converts HTML templates to printer bitmaps."""

    def __init__(self, template_processor: TemplateProcessor) -> None:
        super().__init__()
        self.template_processor = template_processor

    def __get_resource_path(self, name: str):
        path = RESOURCES_DIR / name
        if path.exists():
            return str(path)
        raise ValueError(f"Resource {name} not found at {path}")

    def __generate_temp_file(self, file_name: str) -> Path:
        path = Path(config.app_dirs.user_cache_dir) / "debug"
        ensure_dir(str(path))
        return path / file_name

    def __page_config_css(self, tape_params: TapeInfo, width_px: float | None = None) -> str:
        return PAGE_SIZE_CONFIG_TEMPLATE.format(
            width=f"{tape_params.width_mm}mm", height="9000px" if width_px is None else str(width_px) + "px"
        )

    def __page_set_baseline_font(self, tape_params: TapeInfo) -> str:
        printable_height = tape_params.width_mm - 2 * tape_params.padding_vertical_mm
        return BASELINE_FONT.format(
            size=f"{printable_height}mm",
            line_height=f"{printable_height}mm",
            padding_top=f"{tape_params.padding_vertical_mm}mm",
            padding_bottom=f"{tape_params.padding_vertical_mm}mm",
            padding_left=f"{0}px",
            padding_right=f"{0}px",
        )

    def __find_body_width(self, page: wp.Page) -> float | None:
        try:
            body = page._page_box.all_children()[0].all_children()[0]
            return int(body.width + body.padding_left + body.padding_right)
        except Exception:  # noqa: BLE001
            return None

    def __create_processing_context(self, print_job: PrintJob, tape_params: TapeInfo, is_preview=False):
        return {"params": print_job.params, "param": print_job.params, "tape": tape_params, "is_preview": is_preview}

    def render(self, print_job: PrintJob, tape_params: TapeInfo, is_preview=False, dpi=180):
        """Render a print job to an in-memory PNG file."""
        processing_context = self.__create_processing_context(print_job, tape_params, is_preview)
        label_html = self.template_processor.process(print_job.template, processing_context)

        html = wp.HTML(string=BASE_TEMPLATE.format(content=label_html), media_type="screen" if is_preview else "print")
        # Page Size config
        page_config = self.__page_config_css(tape_params)
        auto_width_mode = True
        stylesheets = [
            wp.CSS(filename=self.__get_resource_path("default.css")),
            wp.CSS(string=self.__page_set_baseline_font(tape_params)),
        ]
        if print_job.template.layout_css is not None:
            label_css = self.template_processor.process_string(
                print_job.template.layout_css, print_job.template.name + "/css", processing_context
            )
            stylesheets.append(wp.CSS(string=label_css))
        if auto_width_mode:
            rendered_label = html.render(stylesheets=stylesheets + [wp.CSS(string=page_config)])
            calculated_width_px = self.__find_body_width(rendered_label.pages[0])
            page_config = self.__page_config_css(tape_params, calculated_width_px)
        rendered_label = html.render(stylesheets=stylesheets + [wp.CSS(string=page_config)])
        result_pdf, result_png = BytesIO(), BytesIO()
        rendered_label.write_pdf(result_pdf, zoom=dpi / DEFAULT_RENDERER_DPI, dpi=dpi)
        pdf = pymupdf.open(stream=result_pdf.getvalue(), filetype="pdf")
        pixmap = pdf.load_page(0).get_pixmap(alpha=True)
        result_png.write(pixmap.tobytes("png"))
        pdf.close()
        result_png.flush()
        result_png.seek(0)
        self.job_num += 1
        if self.persist_rendered_image_as_file:
            path = self.__generate_temp_file(f"rendered-label-{self.job_num}.png")
            with open(path, "wb") as f:
                LOGGER.debug(f"Persisting generated image at {path}")
                f.write(result_png.read())
        return result_png

    def render_bitmap(self, print_job: PrintJob, tape_params: TapeInfo, is_preview=False, dpi=180):
        """Render a print job to a monochrome bitmap image."""
        png = self.render(print_job, tape_params, is_preview, dpi)
        bitmap = Image.open(png, "r", ("png",)).convert("1", dither=0)
        if self.persist_rendered_image_as_file:
            path = self.__generate_temp_file(f"rendered-label-{self.job_num}.bmp")
            LOGGER.debug(f"Persisting rendered bitmap at {path}")
            bitmap.save(path)

        return bitmap
