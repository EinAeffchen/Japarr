import toml
from pathlib import Path

def get_config():
    config_path = Path(__file__).parent/"config.toml"
    return toml.load(config_path)