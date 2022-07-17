import requests
from japarr.adapters.discord import DiscordConnector
from japarr.adapters.base import BaseAdapter
from japarr.logger import get_module_logger

logger = get_module_logger("Sonarr")


class SonarrAdapter(BaseAdapter):
    discord: DiscordConnector
    url: str

    # docs: https://github.com/Sonarr/Sonarr/wiki/Series
    def __init__(self, discord: DiscordConnector):
        super().__init__("sonarr")
        self.discord = discord
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

    def refresh(self, id: int) -> dict:
        command_data = {"name": "RefreshSeries", "seriesId": [id]}
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

    def create(self, overseer_data: dict) -> dict:
        media_info = overseer_data.get("mediaInfo", {})
        tvdb_id = media_info.get("tvdbId")
        if not tvdb_id:
            tvdb_id = overseer_data.get("externalIds", {}).get("tvdbId")
        slugname = overseer_data["name"].replace(" ", "-")
        data = {
            "tvdbId": tvdb_id,
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
        if upload_result.status_code == 400:
            error_json = eval(upload_result.text)[0]
            error = error_json.get("errorMessage")
            value = error_json.get("attemptedValue")
            self.discord.send(
                f"Could not add '{overseer_data['originalName']}' to Sonarr.\n Reason: {error} with value: '{value}'"
            )
            logger.info("Drama could not be added to Sonarr! Reason:")
            logger.info(upload_result.text)
        else:
            self.discord.send(
                f"Added {overseer_data['originalName']} to Sonarr."
            )
