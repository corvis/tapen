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

import yaml


def yaml_file_to_dict(yaml_file: str) -> dict:
    with open(yaml_file, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def dict_to_yaml_file(yaml_dict: dict, yaml_file: str):
    with open(yaml_file, "w") as f:
        return yaml.dump(yaml_dict, f)
