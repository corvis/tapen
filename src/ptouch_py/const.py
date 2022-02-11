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

PTOUCH_ENDPOINT = 0x02
PTOUCH_INPUT_ENDPOINT = 0x81
PTOUCH_STATUS_REPLY_SIZE = 32


CMD_INIT = b"\x1b\x40"
CMD_STATUS_INFO = b"\x1b\x69\x53"
CMD_ENABLE_PACKBITS = b"\x4d\x02"
CMD_DISABLE_PACKBITS = b"\x4d\x00"
CMD_RASTER_START = b"\x1b\x69\x52\x01"
CMD_RASTER_START_P700 = b"\x1b\x69\x61\x01"
CMD_EJECT = b"\x1a"  # print and cut tape
CMD_ADVANCE = b"\x0c"  # print and advance tape, but do not cut
