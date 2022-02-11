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

from ptouch_py.domain import DevInfo

SUPPORTED_DEVICES = [
    DevInfo("PT-P700", 0x04F9, 0x2061, packbits=True, p700_init=True),
    DevInfo("PT-P700 (PLite Mode)", 0x04F9, 0x2064, is_plite=True),
    DevInfo("PT-P750W", 0x04F9, 0x2062, packbits=True, p700_init=True),
    DevInfo("PT-P750W (PLite Mode)", 0x04F9, 0x2065, is_plite=True),
]
