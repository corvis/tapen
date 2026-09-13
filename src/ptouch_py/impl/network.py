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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from html.parser import HTMLParser
import re
import socket
import urllib.request

from ptouch_py.core import Printer, Transport
from ptouch_py.domain import DevInfo, PTStatus, PTStatusRaw


class _TCPTransport(Transport):
    def __init__(self, host: str, port: int = 9100, timeout: float = 10.0) -> None:
        self.socket = socket.create_connection((host, port), timeout=timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.settimeout(timeout)

    def write(self, data: bytes) -> None:
        self.socket.sendall(data)

    def read(self, size: int) -> bytes:
        return self.socket.recv(size)

    def close(self) -> None:
        self.socket.close()


class _WebStatusParser(HTMLParser):
    """Extract the device status from Brother's monitor page."""

    def __init__(self) -> None:
        super().__init__()
        self.status: PTStatus | None = None
        self.media_width: int | None = None
        self._in_status = False
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "span" and "moni" in attributes.get("class", "").split():  # type: ignore[union-attr]
            self._in_status = True

    def handle_data(self, data: str) -> None:
        if self._in_status:
            self._text.append(data)
        media_match = re.search(r"(\d+)mm", data)
        if media_match is not None:
            self.media_width = int(media_match.group(1))
            if self.status is not None:
                self.status.raw.media_width = self.media_width

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._in_status:
            self.status = self._web_status_to_pt_status("".join(self._text).strip(), self.media_width)
            self._in_status = False

    @staticmethod
    def _web_status_to_pt_status(status: str, media_width: int | None) -> PTStatus:
        """Adapt embedded-web status fields to the existing status type."""
        raw = PTStatusRaw()
        raw.printheadmark = 0x80
        raw.size = 0x20
        raw.brother_code = ord("B")
        raw.series_code = ord("0")
        raw.model = ord("h")
        raw.status_type = 0 if status in {"READY", "WAITING"} else 2
        raw.phase_type = 0 if raw.status_type == 0 else 1
        if media_width is not None:
            raw.media_width = media_width
        return PTStatus(raw)


class NetworkPrinter(Printer):
    """Brother P-touch printer connected through a raw TCP/IP port.

    The standard TCP/IP port accepts the same raster command stream as USB.
    Status is read from the printer's embedded web status page.
    """

    def __init__(self, host: str, dev_info: DevInfo, port: int = 9100, timeout: float = 10.0) -> None:
        super().__init__(_TCPTransport(host, port, timeout), dev_info)
        self._host = host
        self._http_timeout = timeout

    @property
    def serial_number(self) -> str:
        """Return a stable network printer identifier."""
        return self.info.name + "@network"

    @property
    def vendor_name(self) -> str:
        """Return the printer vendor name."""
        return "Brother"

    @property
    def product_name(self) -> str:
        """Return the printer model name."""
        return self.info.name

    def init(self) -> None:
        """Initialize the printer for P-touch commands."""
        super().init()

    def get_status(self) -> PTStatus:
        """Return status and tape width from the embedded web status page."""
        request = urllib.request.Request(f"http://{self._host}/general/status.html")
        with urllib.request.urlopen(request, timeout=self._http_timeout) as response:  # noqa: S310
            page = response.read().decode("iso-8859-1")
        parser = _WebStatusParser()
        parser.feed(page)
        if parser.status is None:
            raise ValueError("Printer web status response did not contain device status")
        return parser.status

    def close(self) -> None:
        """Close the network connection."""
        super().close()
