import abc
import argparse
import logging
import sys
from typing import List, Dict, Any

import appdirs
from cli_rack import CLI, ansi
from cli_rack.modular import CliAppManager, CliExtension, GlobalArgsExtension

from tapen import config
from tapen.__version__ import __version__ as VERSION

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

    @classmethod
    def load_config(cls, args: argparse.Namespace) -> Dict[str, Any]:
        return config.load_config(args.config, True)


class ImportLibExtension(BaseCliExtension):
    COMMAND_NAME = "import-lib"
    COMMAND_DESCRIPTION = "Appends new template library to the list of known libraries"

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        parser.add_argument("name", type=str, action="store",
                            help="library name (will be used as prefix for templates)")
        parser.add_argument("url", type=str, action="store", help="library url")

    def handle(self, args: argparse.Namespace):
        config = self.load_config(args)


def main(argv: List[str]):
    CLI.setup()
    CLI.print_info("\nTapen version {}\n".format(VERSION), ansi.Mod.BOLD & ansi.Fg.LIGHT_BLUE)
    app_manager = TapenAppManager("tapen")
    app_manager.parse_and_handle_global()
    # Extensions
    app_manager.register_global_args_extension()
    app_manager.register_extension(ImportLibExtension)
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