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

from typing import Any, Dict, Optional

from tapen import const


class Template:
    def __init__(self, name: str, _dict: Dict[str, Any]) -> None:
        super().__init__()
        self.raw = _dict
        self.name = name

    @property
    def layout_template(self) -> str:
        return self.raw[const.MF_LAYOUT][const.MF_TEMPLATE]

    @property
    def layout_css(self) -> Optional[str]:
        return self.raw[const.MF_LAYOUT].get(const.MF_CSS, None)


class PrintJob(object):
    def __init__(self, template: Template, params: Dict[str, Any], cut_tape=True) -> None:
        self.template = template
        self.params = params
        self.cut_tape = cut_tape
