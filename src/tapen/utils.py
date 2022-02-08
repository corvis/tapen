import yaml


def yaml_file_to_dict(yaml_file: str) -> dict:
    with open(yaml_file, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def dict_to_yaml_file(yaml_dict: dict, yaml_file: str):
    with open(yaml_file, "w") as f:
        return yaml.dump(yaml_dict, f)