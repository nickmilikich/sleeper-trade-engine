import os

from envyaml import EnvYAML

_current_dir = os.path.dirname(__file__)
CONFIG = EnvYAML(os.path.join(_current_dir, "config.yml"))