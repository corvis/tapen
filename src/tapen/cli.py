import abc
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import appdirs
from PIL import Image
from cli_rack import CLI, ansi
from cli_rack.modular import CliAppManager, CliExtension, GlobalArgsExtension
from cli_rack.utils import none_throws

from ptouch_py.core import get_first_printer
from tapen import config, const
from tapen.__version__ import __version__ as VERSION
from tapen.common.domain import PrintJob
from tapen.library import TemplateLibrary
from tapen.printer import get_print_factory, PrinterFactory, TapenPrinter
from tapen.renderer import get_default_renderer, Renderer

LOGGER = logging.getLogger("cli")


class GlobalConfigFile(GlobalArgsExtension):

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument("-c", "--config", type=str, action="store", help="Config file location", default=None)


class TapenAppManager(CliAppManager):

    def __init__(self, prog_name: str = "tapen", add_commands_parser=True, allow_multiple_commands=True,
                 description: str = None,
                 epilog: str = None, **kwargs) -> None:
        super().__init__(prog_name, add_commands_parser, allow_multiple_commands, description, epilog, **kwargs)
        self.register_global_args_extension(GlobalConfigFile)


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
    def load_config(cls, args: argparse.Namespace) -> (str, Dict[str, Any]):
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
        self.__template_library = TemplateLibrary(self.config.get(const.CONF_LIBRARIES),
                                                  always_reload_local_libs=args.debug)

    @property
    def template_library(self) -> TemplateLibrary:
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        if not self.__libs_fetched:
            self.__template_library.fetch_libraries()
        return self.__template_library

    @property
    def renderer(self) -> Renderer:
        if self.__renderer is None:
            self.__renderer = get_default_renderer()
        return self.__renderer

    def get_printer(self) -> TapenPrinter:
        assert self.__printer_factory is not None, "Class is not initialized. Forgot self.init()?"
        return self.__printer_factory.get_first_printer()


class ImportLibExtension(BaseCliExtension):
    COMMAND_NAME = "import-lib"
    COMMAND_DESCRIPTION = "Appends new template library to the list of known libraries"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument("name", type=str, action="store",
                            help="library name (will be used as prefix for templates)")
        parser.add_argument("url", type=str, action="store", help="library url")

    def handle(self, args: argparse.Namespace):
        self.init(args)
        CLI.print_info("Adding library \"{}\" (endpoint {})...".format(args.name, args.url))
        self.template_library.add_library(args.name, args.url)
        self.config.get(const.CONF_LIBRARIES)[args.name] = args.url
        self.persist_config()
        CLI.print_info("Library {} has been added to config file".format(args.name))


class PrintExtension(BaseCliExtension):
    COMMAND_NAME = "print"
    COMMAND_DESCRIPTION = "Renders and prints given data"
    DEFAULT_TEMPLATE_NAME = "std:default"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument("template", action="store", help="Template to use")
        parser.add_argument("data", nargs="*", action="store", help="Data to be printed (will be passed into template)")

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
        if printer is None:
            CLI.print_error("Printer is not connected.")
            exit(1)
        else:
            CLI.print_info("Detected printer: {}".format(printer))
        printer.init()
        printer_status = printer.get_status()
        CLI.print_info("\tTape: {}".format(printer_status.tape_info))
        for x in data:
            print_job = PrintJob(template, dict(default=x), cut_tape=False)
            bitmap = self.renderer.render_bitmap(print_job, printer_status.tape_info)
            printer.print_image(bitmap, print_job.cut_tape)


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


def entrypoint():
    main(sys.argv[1:])


if __name__ == "__main__":
    entrypoint()
