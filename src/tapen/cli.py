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

import abc
import argparse
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from cli_rack import CLI, ansi
from cli_rack.modular import CliAppManager, CliExtension, GlobalArgsExtension
from cli_rack.utils import none_throws

from tapen import config, const
from tapen.__version__ import __version__ as VERSION
from tapen.common.domain import PrintJob
from tapen.library import TemplateLibrary
from tapen.printer import get_print_factory, PrinterFactory, TapenPrinter
from tapen.printer.common import PrintingMode, TapeInfo
from tapen.renderer import get_default_renderer, Renderer

LOGGER = logging.getLogger("cli")


class EnumAction(argparse.Action):
    """
    Argparse action for handling Enums
    """

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

        super(EnumAction, self).__init__(**kwargs)

        self._enum = enum_type

    def __call__(self, parser, namespace, values, option_string=None):
        # Convert value back into an Enum
        value = self._enum(values)
        setattr(namespace, self.dest, value)


class GlobalConfigFile(GlobalArgsExtension):
    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument("-c", "--config", type=str, action="store", help="Config file location", default=None)


class TapenAppManager(CliAppManager):
    def __init__(
        self,
        prog_name: str = "tapen",
        add_commands_parser=True,
        allow_multiple_commands=True,
        description: str = None,
        epilog: str = None,
        **kwargs,
    ) -> None:
        super().__init__(prog_name, add_commands_parser, allow_multiple_commands, description, epilog, **kwargs)
        self.register_global_args_extension(GlobalConfigFile)
        self.allow_multiple_commands = False


class BaseCliExtension(CliExtension, metaclass=abc.ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__template_library: Optional[TemplateLibrary] = None
        self.__config: Optional[Dict[str, Any]] = None
        self.__config_location: Optional[str] = None
        self.__renderer: Optional[Renderer] = None
        self.__printer_factory: Optional[PrinterFactory] = None
        self.__libs_fetched = False

    @classmethod
    def load_config(cls, args: argparse.Namespace) -> Tuple[str, Dict[str, Any]]:
        return config.load_config(args.config, True)

    def persist_config(self):
        config.write_config_file(self.config, Path(none_throws(self.__config_location)))

    @property
    def config(self) -> Dict[str, Any]:
        assert self.__config is not None, "Class is not initialized. Forgot self.init()?"
        return self.__config

    def init(self, args: argparse.Namespace):
        self.__config_location, self.__config = self.load_config(args)
        self.__renderer = get_default_renderer()
        if args.debug:
            self.__renderer.persist_rendered_image_as_file = True
        self.__printer_factory = get_print_factory()
        self.__template_library = TemplateLibrary(
            self.config.get(const.CONF_LIBRARIES), always_reload_local_libs=args.debug  # type: ignore
        )

    @property
    def template_library(self) -> TemplateLibrary:
        assert (
            self.__printer_factory is not None and self.__template_library is not None
        ), "Class is not initialized. Forgot self.init()?"
        if not self.__libs_fetched:
            self.__template_library.fetch_libraries()
        return self.__template_library

    @property
    def renderer(self) -> Renderer:
        if self.__renderer is None:
            self.__renderer = get_default_renderer()
        return self.__renderer

    def get_printer(self) -> Optional[TapenPrinter]:
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        return self.__printer_factory.get_first_printer()

    def get_cached_tape_info(self, printer_id: Optional[str] = None) -> Optional[TapeInfo]:
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        return self.__printer_factory.get_cached_tape_info(printer_id)


class ImportLibExtension(BaseCliExtension):
    COMMAND_NAME = "import-lib"
    COMMAND_DESCRIPTION = "Appends new template library to the list of known libraries"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument(
            "name", type=str, action="store", help="library name (will be used as prefix for templates)"
        )
        parser.add_argument("url", type=str, action="store", help="library url")

    def handle(self, args: argparse.Namespace):
        self.init(args)
        CLI.print_info('Adding library "{}" (endpoint {})...'.format(args.name, args.url))
        self.template_library.add_library(args.name, args.url)
        self.config.get(const.CONF_LIBRARIES)[args.name] = args.url  # type:ignore
        self.persist_config()
        CLI.print_info("Library {} has been added to config file".format(args.name))


class PrintExtension(BaseCliExtension):
    COMMAND_NAME = "print"
    COMMAND_DESCRIPTION = "Renders and prints given data"
    DEFAULT_TEMPLATE_NAME = "std:default"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
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
        parser.add_argument("template", action="store", type=str, help="Template to use")
        parser.add_argument(
            "data", nargs="*", action="store", type=str, help="Data to be printed (will be passed into template)"
        )

    def __is_template_name(self, name: str) -> bool:
        return ":" in name

    def handle(self, args: argparse.Namespace):
        self.init(args)
        template_name = args.template
        data = args.data
        if not self.__is_template_name(template_name):
            data = [template_name] + data
            template_name = self.DEFAULT_TEMPLATE_NAME
        template = self.template_library.load_template(template_name)
        # Load printer data
        printer = self.get_printer()
        if printer is None and not args.skip_printing:
            CLI.print_error("Printer is not connected.")
            exit(1)
        else:
            if printer is not None:
                CLI.print_info("Detected printer: {}".format(printer))
                printer.init()
        tape_info = self.get_cached_tape_info()
        if tape_info is None or args.force_tape_detection:
            if not args.skip_printing or args.force_tape_detection:
                printer_status = none_throws(printer).get_status()
                CLI.print_info("\tTape: {}".format(printer_status.tape_info))
                tape_info = printer_status.tape_info
            else:
                if args.skip_printing:
                    CLI.print_error("Tape information is not available in cache. Skip printing mode is not available")
                    exit(2)
        else:
            CLI.print_info("Assuming tape: {}".format(tape_info))
        label_num = 0
        if len(data) == 0:
            data = [None]
        total_labels = len(data) * args.copies
        for i, x in enumerate(data):
            print_job = PrintJob(template, dict(default=x))
            bitmap = self.renderer.render_bitmap(print_job, none_throws(tape_info))
            if not args.skip_printing:
                for c in range(args.copies):
                    label_num += 1
                    if args.mode == PrintingMode.HALF_CUT:
                        cut_tape = label_num == total_labels  # Cut the last label
                    else:
                        cut_tape = True
                    none_throws(printer).print_image(bitmap, cut_tape)
            else:
                CLI.print_warn("Printing skipped as per user request.")


class TppExtension(GlobalArgsExtension):
    def __init__(self, app_manager: Optional["CliAppManager"] = None) -> None:
        super().__init__(app_manager)
        self.__printExt = PrintExtension()

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        PrintExtension.setup_parser(parser)

    def handle(self, args):
        self.__printExt.handle(args)


def main(argv: List[str]):
    CLI.setup()
    CLI.print_info("\nTapen version {}\n".format(VERSION), ansi.Mod.BOLD & ansi.Fg.LIGHT_BLUE)
    app_manager = TapenAppManager("tapen")
    app_manager.parse_and_handle_global()
    # Extensions
    app_manager.register_global_args_extension()
    app_manager.register_extension(ImportLibExtension)
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
    except Exception as e:
        CLI.print_error(e)


def main_tpp(argv: List[str]):
    CLI.setup()
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
    except Exception as e:
        CLI.print_error(e)


def default_entrypoint():
    main(sys.argv[1:])


def tpp_entrypoint():
    main_tpp(sys.argv[1:])


if __name__ == "__main__":
    default_entrypoint()
