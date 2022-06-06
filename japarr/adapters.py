from ast import parse
from distutils.command.upload import upload
from japarr.logger import get_module_logger
from japarr.discord import discord_writer
from typing import Optional
import toml
from pathlib import Path
import requests


logger = get_module_logger("Adapters")


class BaseAdapter:
    def _load_config(self, system: str):
        try:
            self.system = system
            config_path = Path(__file__).parent / "config"
            cfg = toml.load(config_path / "config.toml")
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
                "Not all necessary settings set for system: %s.\n Please check your config.toml",
                system,
            )

    def _test_connection(self):
        status = requests.get(
            f"{self.url}/system/status", headers=self.headers
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
        self._load_config(system)
        self._test_connection()


class OverseerAdapter(BaseAdapter):
    # docs: https://api-docs.overseerr.dev/#/search/get_search
    def __init__(self):
        super().__init__("overseer")

    def search(self, query: str) -> Optional[dict]:
        results = requests.get(
            f"{self.url}/v1/search?query=={query}&language=jp",
            headers=self.headers,
        )
        if results.status_code == 200:
            result_json = results.json()
            for result in result_json.get("results", []):
                if "JP" in result.get("originCountry", []):
                    if result.get("mediaType") == "tv":
                        return self.get_tv_details(result["id"])
                    else:
                        return self.get_movie_details(result["id"])
        else:
            logger.info("No results found for search: '%s'", query)

    def get_tv_details(self, id: int):
        results = requests.get(
            f"{self.url}/v1/tv/{id}",
            headers=self.headers,
        )
        if results.status_code == 200:
            return results.json()
        else:
            logger.info("Couldn't find details to tvshow id: %s", id)

    def get_movie_details(self, id: int):
        results = requests.get(
            f"{self.url}/v1/movie/{id}",
            headers=self.headers,
        )
        if results.status_code == 200:
            return results.json()
        else:
            logger.info("Couldn't find details to movie id: %s", id)


class SonarrAdapter(BaseAdapter):
    # docs: https://github.com/Sonarr/Sonarr/wiki/Series
    def __init__(self):
        super().__init__("sonarr")
        if not self.root_folder:
            self._set_root_folder()

    def _set_root_folder(self):
        folder_request = requests.get(
            f"{self.url}/rootfolder", headers=self.headers
        )
        if folder_request.status_code == 200:
            folder_json = folder_request.json()
            try:
                self.root_folder = folder_json[0]["path"]
            except KeyError:
                logger.warning(
                    "Couldn't retrieve rootfolder! Either set rootfolder via config 'root_folder' or make sure the /rootfolder api endpoint is reachable!"
                )
                exit

    def _parse_season(self, season: dict) -> dict:
        parsed_season = dict()
        parsed_season["seasonNumber"] = season["seasonNumber"]
        parsed_season["monitored"] = False
        parsed_season["statistics"] = {
            "previousAiring": season["airDate"],
            "totalEpisodeCount": season["episodeCount"],
        }
        return parsed_season

    def create(self, overseer_data: dict) -> dict:
        media_info = overseer_data.get("mediaInfo", {})
        slugname = overseer_data["name"].replace(" ", "-")
        data = {
            "tvdbId": media_info.get("tvdbId"),
            "title": overseer_data["originalName"],
            "profileId": self.profile_id,
            "titleSlug": slugname,
            "path": f"{self.root_folder}{slugname}",
            "monitored": self.automonitor,
            "seasonFolder": self.season_folder,
            "images": [
                {
                    "coverType": "poster",
                    "remoteUrl": f"https://image.tmdb.org/t/p/w600_and_h900_bestv2/{overseer_data['posterPath']}.jpg",
                },
                {
                    "coverType": "banner",
                    "remoteUrl": f"https://image.tmdb.org/t/p/w1920_and_h800_multi_faces//{overseer_data['backdropPath']}.jpg",
                },
            ],
            "seasons": [
                self._parse_season(season)
                for season in overseer_data["seasons"]
            ],
            "addOptions": {
                "ignoreEpisodesWithFiles": True,
                "ignoreEpisodesWithoutFiles": False,
            },
        }
        upload_result = requests.post(
            f"{self.url}/series", json=data, headers=self.headers
        )
        if upload_result.status_code==400:
            discord_writer.send(f"Could not add '{overseer_data['originalName']}' to Sonarr. Check logs for traceback.")
            logger.info("Drama could not be added to Sonarr! Reason:")
            logger.info(upload_result.text)
        else:
            discord_writer.send(f"Added {overseer_data['originalName']} to Sonarr.")
        # logger.debug("Show Creation result: %s", upload_result)


class RadarrAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("radarr")
