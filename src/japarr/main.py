#!/usr/bin/env python
# coding: utf-8
from japarr.adapters.overseer import OverseerAdapter
from japarr.adapters.sonarr import SonarrAdapter
from japarr.adapters.radarr import RadarrAdapter
from japarr.adapters.discord import DiscordConnector
from japarr.db import JaparrDB
from japarr.adapters.jraws import JRawsDownloader
from japarr.logger import get_module_logger

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
        self.jraw_adapter = JRawsDownloader(self.discord)
        self.active = True
        self.logger = get_module_logger("DownloadManager")

    def start_movies(self):
        next_page = 1
        while next_page:
            movies, next_page = self.jraw_adapter.get_movies(next_page)
            for movie in movies:
                if self.db.get_movie(movie.title):
                    self.logger.info(
                        "Already downloaded %s, skipping!", movie.title
                    )
                    continue
                self.logger.debug("Movie: %s", vars(movie))
                if not self.active:
                    return
                self.logger.debug("Searching for movie %s", movie.title)
                media_detail_dict = self.jraw_adapter.parse_media_details(
                    movie.url
                )
                movie.set_media_details(media_detail_dict)
                search_result = self.overseerr.search(
                    movie=movie, is_anime=False
                )
                if search_result:
                    radarr_obj = self.radarr.create(search_result)
                if not search_result or radarr_obj["sizeOnDisk"] < 1:
                    movie.folder = radarr_obj["folderName"]
                    for _ in movie.download_files():
                        self.db.add_movie(movie.title, movie.url)
                        if movie_id := radarr_obj.get("id"):
                            result = self.radarr.refresh(movie_id)
                            self.discord.send(
                                f"Triggered autorefresh on {movie.title}: {result.get('message')}"
                            )
                else:
                    self.logger.info(
                        f"Movie {movie.title} already exists, skipping download!"
                    )
                    self.db.add_movie(movie.title, movie.url)

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
