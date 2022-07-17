import json
from datetime import datetime
from typing import Optional

import requests
from japarr.adapters.discord import DiscordConnector
from japarr.adapters.base import BaseAdapter
from japarr.logger import get_module_logger

logger = get_module_logger("Radarr")


class RadarrAdapter(BaseAdapter):
    def __init__(self, discord: DiscordConnector):
        super().__init__("radarr")
        self.discord = discord
        if not self.root_folder:
            self._set_root_folder()

    def _set_root_folder(self):
        folder_request = requests.get(
            f"{self.url}/v3/rootFolder", headers=self.headers
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

    def _get_create_dict(self, tmdb_id: int) -> Optional[dict]:
        detail_request = requests.get(
            f"{self.url}/v3/movie/lookup?term=tmdb:{tmdb_id}",
            headers=self.headers,
        )
        if detail_request.status_code == 200:
            create_json = detail_request.json()
            if create_json:
                return create_json[0]

    def refresh(self, id: int) -> dict:
        command_data = {"name": "RefreshMovie", "movieIds": [id]}
        command = requests.post(
            f"{self.url}/v3/command",
            headers=self.headers,
            json=command_data,
        )
        if command.status_code == 201:
            return command.json()
        else:
            logger.warning("Couldn't autorefresh due to %s", command.text)
            return dict()

    def create(self, overseer_data: dict) -> Optional[int]:
        tmdbid = overseer_data["id"]
        create_data = self._get_create_dict(tmdbid)
        today = datetime.now()
        release = datetime.strptime(overseer_data["releaseDate"], "%Y-%m-%d")
        create_data["added"] = today.isoformat()
        create_data["digitalRelease"] = release.isoformat()
        create_data["imdbId"] = overseer_data.get("imdbId")
        create_data["minimumAvailability"] = "released"
        create_data["qualityProfileId"] = self.profile_id
        create_data["rootFolderPath"] = self.root_folder
        if create_data["sizeOnDisk"] > 0:
            return create_data
        upload_result = requests.post(
            f"{self.url}/v3/movie", json=create_data, headers=self.headers
        )
        if upload_result.status_code == 400:
            error_json = json.loads(upload_result.text)
            if isinstance(error_json, list):
                error_json = error_json[0]
            error = error_json.get("errorMessage")
            self.discord.send(
                f"Could not add '{overseer_data['originalTitle']}' to Radarr.\n Reason: {error}"
            )
            logger.info("Movie could not be added to Radarr! Reason:")
            logger.info(upload_result.text)
            return create_data
        else:
            self.discord.send(
                f"Added {overseer_data['originalTitle']} to Radarr."
            )
            return upload_result.json()
