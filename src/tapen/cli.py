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

import abc
import argparse
import copy
from enum import Enum
import ipaddress
import logging
from pathlib import Path
import re
import sys
from typing import Any

from cli_rack import CLI, ansi
from cli_rack.modular import CliAppManager, CliExtension, GlobalArgsExtension
from cli_rack.utils import none_throws

from tapen import config, const
from tapen.__version__ import __version__ as VERSION
from tapen.common.domain import PrintJob
from tapen.library import STANDARD_LIB_NAME, TemplateLibrary
from tapen.printer import PrinterFactory, TapenPrinter, get_print_factory
from tapen.printer.common import PrintingMode, TapeInfo
from tapen.renderer import Renderer, get_default_renderer

LOGGER = logging.getLogger("cli")


class EnumAction(argparse.Action):
    """Argparse action for handling enums."""

    def __init__(self, **kwargs):
        # Pop off the type value
        enum_type = kwargs.pop("type", None)

        # Ensure an Enum subclass is provided
        if enum_type is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        if not issubclass(enum_type, Enum):
            raise TypeError("type must be an Enum when using EnumAction")

        # Generate choices from the Enum
        kwargs.setdefault("choices", tuple(e.value for e in enum_type))

        super().__init__(**kwargs)

        self._enum = enum_type

    def __call__(self, parser, namespace, values, option_string=None):
        """Store the parsed enum value on the argparse namespace."""
        # Convert value back into an Enum
        value = self._enum(values)
        setattr(namespace, self.dest, value)


class GlobalConfigFile(GlobalArgsExtension):
    """Global extension that adds the config file argument."""

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        """Configure global config-file CLI arguments."""
        parser.add_argument("-c", "--config", type=str, action="store", help="Config file location", default=None)


class TapenAppManager(CliAppManager):
    """Application manager configured for Tapen commands."""

    def __init__(
        self,
        prog_name: str = "tapen",
        add_commands_parser: bool = True,
        allow_multiple_commands: bool = True,
        description: str | None = None,
        epilog: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(prog_name, add_commands_parser, allow_multiple_commands, description, epilog, **kwargs)
        self.register_global_args_extension(GlobalConfigFile)
        self.allow_multiple_commands = False


class BaseCliExtension(CliExtension, metaclass=abc.ABCMeta):
    """Base class for Tapen CLI extensions."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.__template_library: TemplateLibrary | None = None
        self.__config: dict[str, Any] | None = None
        self.__config_location: str | None = None
        self.__renderer: Renderer | None = None
        self.__printer_factory: PrinterFactory | None = None
        self.__libs_fetched = False

    @classmethod
    def load_config(cls, args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
        """Load the application configuration for CLI arguments."""
        return config.load_config(args.config, True)

    def persist_config(self):
        """Write the current configuration to disk."""
        config_obj = copy.deepcopy(self.config)
        # Do not include standard library into config file
        libraries = config_obj.get(const.CONF_LIBRARIES, {})
        if STANDARD_LIB_NAME in libraries:
            del libraries[STANDARD_LIB_NAME]
        config.write_config_file(config_obj, Path(none_throws(self.__config_location)))

    @property
    def config(self) -> dict[str, Any]:
        """Return the initialized application configuration."""
        assert self.__config is not None, "Class is not initialized. Forgot self.init()?"
        return self.__config

    def init(self, args: argparse.Namespace):
        """Initialize shared CLI dependencies from parsed arguments."""
        self.__config_location, self.__config = self.load_config(args)
        self.__renderer = get_default_renderer()
        if args.debug:
            self.__renderer.persist_rendered_image_as_file = True
        self.__printer_factory = get_print_factory(self.config.get(const.CONF_PRINTERS, []))
        libraries: dict[str, Any] = self.config.get(const.CONF_LIBRARIES, {})
        self.__template_library = TemplateLibrary(libraries, always_reload_local_libs=args.debug)

    @property
    def template_library(self) -> TemplateLibrary:
        """Return the initialized template library."""
        assert self.__printer_factory is not None and self.__template_library is not None, (
            "Class is not initialized. Forgot self.init()?"
        )
        if not self.__libs_fetched:
            self.__template_library.fetch_libraries()
        return self.__template_library

    @property
    def renderer(self) -> Renderer:
        """Return the renderer instance."""
        if self.__renderer is None:
            self.__renderer = get_default_renderer()
        return self.__renderer

    def get_printer(self, printer_name: str | None = None) -> TapenPrinter | None:
        """Return the selected or default discovered printer, if available."""
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        if printer_name == "usb":
            usb_printers = self.__printer_factory.discover_usb_printers()
            if not usb_printers:
                CLI.fail("No USB printer is connected", 1)
            return usb_printers[0]
        configured = None
        if printer_name is not None:
            configured = next(
                (
                    printer
                    for printer in self.config.get(const.CONF_PRINTERS, [])
                    if printer[const.CONF_NAME] == printer_name
                ),
                None,
            )
            if configured is None:
                CLI.fail(f'Printer "{printer_name}" is not registered in the configuration', 1)
        printers = self.__printer_factory.discover_printers()
        if printer_name is not None:
            assert configured is not None
            return next((printer for printer in printers if printer.id == configured[const.CONF_ADDRESS]), None)
        default_name = self.config.get(const.CONF_DEFAULT_PRINTER)
        if default_name is not None:
            default = next(
                (
                    printer
                    for printer in self.config.get(const.CONF_PRINTERS, [])
                    if printer[const.CONF_NAME] == default_name
                ),
                None,
            )
            if default is not None:
                return next((printer for printer in printers if printer.id == default[const.CONF_ADDRESS]), None)
        return printers[0] if printers else None

    def discover_printers(self) -> list[TapenPrinter]:
        """Return printers currently discovered by the active factory."""
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        return self.__printer_factory.discover_printers()

    def discover_usb_printers(self) -> list[TapenPrinter]:
        """Return currently connected USB printers."""
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        return self.__printer_factory.discover_usb_printers()

    def get_cached_tape_info(self, printer_id: str | None = None) -> TapeInfo | None:
        """Return cached tape information for a printer."""
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        return self.__printer_factory.get_cached_tape_info(printer_id)


class ImportLibExtension(BaseCliExtension):
    """CLI extension for importing template libraries."""

    COMMAND_NAME = "import-lib"
    COMMAND_DESCRIPTION = "Appends new template library to the list of known libraries"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        """Configure arguments for importing a template library."""
        parser.add_argument(
            "name", type=str, action="store", help="library name (will be used as prefix for templates)"
        )
        parser.add_argument(
            "url",
            type=str,
            action="store",
            help="library locator e.g local:/your/path/to/lib or github://user/repo@tagorbranch",
        )

    def handle(self, args: argparse.Namespace):
        """Import a template library into the configuration."""
        self.init(args)
        CLI.print_info(f'Adding library "{args.name}" (endpoint {args.url})...')
        self.template_library.add_library(args.name, args.url)
        self.config.get(const.CONF_LIBRARIES)[args.name] = args.url  # type:ignore
        self.persist_config()
        CLI.print_info(f"Library {args.name} has been added to config file")


class PrintersExtension(BaseCliExtension):
    """Manage printers stored in the Tapen configuration."""

    COMMAND_NAME = "printers"
    COMMAND_DESCRIPTION = "Manage configured printers"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        """Configure printer management subcommands."""
        commands = parser.add_subparsers(dest="printers_command", required=True)
        add = commands.add_parser("add", help="Add a printer to the configuration")
        add.add_argument("name", help="Configuration name")
        add.add_argument("address", help="USB serial number or network IP address")
        add.add_argument("--type", choices=("usb", "network"), default=None)
        add.add_argument("--verbose-name", default=None)
        add.add_argument("--description", default=None)
        commands.add_parser("list", help="List configured and discovered printers")

    def handle(self, args: argparse.Namespace):  # noqa: C901
        """Execute a printer management subcommand."""
        self.init(args)
        printers = self.config.setdefault(const.CONF_PRINTERS, [])
        if args.printers_command == "add":
            if any(printer[const.CONF_NAME] == args.name for printer in printers):
                raise ValueError(f'Printer name "{args.name}" is already configured')
            printer_type = args.type
            if printer_type is None:
                try:
                    ipaddress.ip_address(args.address)
                    printer_type = "network"
                except ValueError:
                    printer_type = (
                        "usb"
                        if (
                            args.address.startswith(("usb:", "/dev/"))
                            or re.fullmatch(r"\d+[/ :]\d+", args.address) is not None
                        )
                        else "network"
                    )
            printer = {
                const.CONF_NAME: args.name,
                const.CONF_TYPE: printer_type,
                const.CONF_ADDRESS: args.address,
            }
            if args.verbose_name is not None:
                printer[const.CONF_VERBOSE_NAME] = args.verbose_name
            if args.description is not None:
                printer[const.CONF_DESCRIPTION] = args.description
            printers.append(printer)
            self.persist_config()
            CLI.print_info(f'Printer "{args.name}" has been added to config file')
            return

        discovered_usb = {printer.id: printer for printer in self.discover_usb_printers()}
        CLI.print_info("Configured printers:")
        for printer in printers:
            if printer[const.CONF_TYPE] == "usb":
                state = "connected" if printer[const.CONF_ADDRESS] in discovered_usb else "not connected"
            else:
                state = "configured"
            display_name = printer.get(const.CONF_VERBOSE_NAME, printer[const.CONF_NAME])
            CLI.print_info(f"  {display_name} [{printer[const.CONF_TYPE]}] {printer[const.CONF_ADDRESS]} ({state})")
            if printer.get(const.CONF_DESCRIPTION):
                CLI.print_info(f"    {printer[const.CONF_DESCRIPTION]}")
        CLI.print_info("Discovered USB printers:")
        configured_addresses = {
            printer[const.CONF_ADDRESS] for printer in printers if printer[const.CONF_TYPE] == "usb"
        }
        for address, discovered_printer in discovered_usb.items():
            configured = "configured" if address in configured_addresses else "not configured"
            CLI.print_info(f"  {discovered_printer} [{address}] ({configured})")
        if not discovered_usb:
            CLI.print_info("  none")


class PrintExtension(BaseCliExtension):
    """CLI extension for rendering and printing labels."""

    COMMAND_NAME = "print"
    COMMAND_DESCRIPTION = "Renders and prints given data"
    DEFAULT_TEMPLATE_NAME = "std:default"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        """Configure arguments for rendering and printing labels."""
        parser.add_argument(
            "-m",
            "--mode",
            action=EnumAction,
            type=PrintingMode,  # type: ignore
            choices=[x.value for x in PrintingMode],
            default=PrintingMode.HALF_CUT,
            help="Print mode (applicable for for more than one labels only)",
        )
        parser.add_argument(
            "-q",
            "--copies",
            action="store",
            type=int,
            default=1,
            help="Quantity of copies of each label",
        )
        parser.add_argument(
            "-f",
            "--force-tape-detection",
            action="store_true",
            default=False,
            help="Forces tape detection even though there is a cached data",
        )
        parser.add_argument(
            "-s",
            "--skip-printing",
            action="store_true",
            default=False,
            help="Renders data and skips printing on the real device",
        )
        parser.add_argument(
            "-p",
            "--printer",
            type=str,
            default=None,
            help='Printer name from config or "usb" for the first discovered USB printer',
        )
        parser.add_argument("template", action="store", type=str, help="Template to use")
        parser.add_argument(
            "data", nargs="*", action="store", type=str, help="Data to be printed (will be passed into template)"
        )

    def __is_template_name(self, name: str) -> bool:
        return ":" in name

    def handle(self, args: argparse.Namespace):  # noqa: C901
        """Render and optionally print labels from CLI arguments."""
        self.init(args)
        template_name = args.template
        data = args.data
        if not self.__is_template_name(template_name):
            data = [template_name] + data
            template_name = self.DEFAULT_TEMPLATE_NAME
        template = self.template_library.load_template(template_name)
        # Load printer data
        printer = self.get_printer(args.printer)
        if printer is None and not args.skip_printing:
            CLI.print_error("Printer is not connected.")
            sys.exit(1)
        else:
            if printer is not None:
                CLI.print_info(f"Detected printer: {printer}")
                printer.init()
        tape_info = self.get_cached_tape_info()
        if tape_info is None or args.force_tape_detection:
            if not args.skip_printing or args.force_tape_detection:
                printer_status = none_throws(printer).get_status()
                CLI.print_info(f"\tTape: {printer_status.tape_info}")
                tape_info = printer_status.tape_info
            else:
                if args.skip_printing:
                    CLI.print_error("Tape information is not available in cache. Skip printing mode is not available")
                    sys.exit(2)
        else:
            CLI.print_info(f"Assuming tape {tape_info}")
        label_num = 0
        if len(data) == 0:
            data = [None]
        total_labels = len(data) * args.copies
        for x in data:
            print_job = PrintJob(template, {"default": x})
            bitmap = self.renderer.render_bitmap(print_job, none_throws(tape_info))
            if not args.skip_printing:
                for _ in range(args.copies):
                    label_num += 1
                    if args.mode == PrintingMode.HALF_CUT:
                        cut_tape = label_num == total_labels  # Cut the last label
                    else:
                        cut_tape = True
                    none_throws(printer).print_image(bitmap, cut_tape)
            else:
                CLI.print_warn("Printing skipped as per user request.")


class TppExtension(GlobalArgsExtension):
    """Global extension for the legacy `tpp` entrypoint."""

    def __init__(self, app_manager: CliAppManager | None = None) -> None:
        super().__init__(app_manager)
        self.__printExt = PrintExtension()

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        """Configure print arguments for the `tpp` entrypoint."""
        PrintExtension.setup_parser(parser)

    def handle(self, args):
        """Delegate handling to the print extension."""
        self.__printExt.handle(args)


def _configure_logger():
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    logging.getLogger("PIL").setLevel(logging.INFO)


def main(argv: list[str]):
    """Run the main Tapen CLI entrypoint."""
    CLI.setup()
    _configure_logger()
    CLI.print_info(f"\nTapen version {VERSION}\n", ansi.Mod.BOLD & ansi.Fg.LIGHT_BLUE)
    app_manager = TapenAppManager("tapen")
    app_manager.parse_and_handle_global()
    # Extensions
    app_manager.register_global_args_extension()
    app_manager.register_extension(ImportLibExtension)
    app_manager.register_extension(PrintersExtension)
    app_manager.register_extension(PrintExtension)
    app_manager.setup()
    try:
        # Parse arguments
        parsed_commands = app_manager.parse(argv)
        if len(parsed_commands) == 1 and parsed_commands[0].cmd is None:
            app_manager.args_parser.print_help()
            CLI.fail("At least one command is required", 7)
        # Run
        exec_manager = app_manager.create_execution_manager()
        exec_manager.run(parsed_commands)
    except Exception as e:  # noqa: BLE001
        CLI.print_error(e)


def main_tpp(argv: list[str]):
    """Run the compatibility `tpp` CLI entrypoint."""
    CLI.setup()
    _configure_logger()
    app_manager = TapenAppManager("tapen")
    app_manager.parse_and_handle_global()
    app_manager.register_global_args_extension(TppExtension)
    app_manager.add_commands_parser = False
    app_manager.setup()
    try:
        # Parse arguments
        parsed_commands = app_manager.parse(argv)
        ext = TppExtension()
        ext.handle(parsed_commands[0])
    except Exception as e:  # noqa: BLE001
        CLI.print_error(e)


def default_entrypoint():
    """Invoke the default console-script entrypoint."""
    main(sys.argv[1:])


def tpp_entrypoint():
    """Invoke the `tpp` console-script entrypoint."""
    main_tpp(sys.argv[1:])


if __name__ == "__main__":
    default_entrypoint()
