from japarr.logger import get_module_logger
import requests
from japarr.config.config import get_config
logger = get_module_logger("Adapters")

class BaseAdapter:
    url: str
    system: str
    profile_id: int
    automonitor: bool
    season_folder: bool
    root_folder: str
    tags: list
    active: bool

    def _load_config(self, system: str):
        try:
            self.system = system
            cfg = get_config()
            system_cfg = cfg[self.system]
            self.url = f'{system_cfg["protocol"]}://{system_cfg["host"]}:{system_cfg["port"]}/api'
            self.headers = {
                "X-Api-Key": system_cfg["api_key"],
                "accept": "application/json",
            }
            if def_profile := cfg[self.system].get("default_profile", 1):
                self.profile_id = def_profile
            if automonitor := cfg[self.system].get("automonitor", False):
                self.automonitor = automonitor
            if season_folder := cfg[self.system].get("season_folder", False):
                self.season_folder = season_folder
            if optional_cfg := cfg[self.system].get("optional", {}):
                for key, value in optional_cfg.items():
                    setattr(self, key, value)
        except KeyError:
            logger.error(
                "Not all necessary settings set for system: %s.\n Please check your config.toml.\nJaparr will run without the connection",
                system,
            )
            self.active = False

    def _test_connection(self):
        status = requests.get(
            f"{self.url}/v3/system/status", headers=self.headers
        )
        if status.status_code == 200:
            logger.debug(
                "%s status is running and api is reachable!", self.system
            )
        else:
            logger.warning(
                "%s is not reachable. Statuscode: %s",
                self.system,
                status.status_code,
            )

    def __init__(self, system: str):
        self.active = True
        self._load_config(system)
        self._test_connection()