import toml
from pathlib import Path

from .model.config import Config

config_path = Path("config.toml")


if not config_path.exists():
    config = Config()
    config_path.write_text(toml.dumps(config.dict()))
    raise Exception("Please edit config.toml")

config = Config(**toml.load(Path("config.toml")))
