#!/usr/bin/env python
# coding: utf-8
from japarr.adapters.overseer import OverseerAdapter
from japarr.adapters.sonarr import SonarrAdapter
from japarr.adapters.radarr import RadarrAdapter
from japarr.adapters.discord import DiscordConnector
from japarr.db import JaparrDB
from japarr.adapters.jraws import JRawsDownloader

from japarr.media_objects import Movie, Drama


class DownloadManager:
    discord = DiscordConnector
    sonarr = SonarrAdapter
    radarr = RadarrAdapter
    overseerr = OverseerAdapter
    db = JaparrDB
    jraw_adapter = JRawsDownloader
    active = bool

    def __init__(self) -> None:
        self.discord = DiscordConnector()
        self.sonarr = SonarrAdapter(self.discord)
        self.radarr = RadarrAdapter(self.discord)
        self.overseerr = OverseerAdapter()
        self.db = JaparrDB()
        self.jraw_adapter = JRawsDownloader()
        self.active = True

    def start_movies(self):
        movies = self.jraw_adapter.get_movies()
        for movie in movies:
            if not self.active:
                return
            search_result = self.overseerr.search(
                query=movie.title, is_anime=False
            )
            self.radarr.create(search_result)
            media_detail_dict = self.jraw_adapter.parse_media_details(
                movie.url
            )
            movie.set_media_details(media_detail_dict)
            for downloaded_file in movie.download_files():
                self.db.add_movie(downloaded_file["title"], movie.url)

    def start_dramas(self):
        """
        Still has to be implemented
        """
        pass

    def start_anime(self):
        """
        Still has to be implemented
        """
        pass

    def start(self):
        self.active = True
        self.start_movies()
        self.start_dramas()
        self.start_anime()

    def stop(self):
        self.active = False


if __name__ == "__main__":
    dm = DownloadManager()
    dm.start()
