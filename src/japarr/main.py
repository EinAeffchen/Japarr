#!/usr/bin/env python
# coding: utf-8
from typing import List, Tuple
from japarr.adapters.overseer import OverseerAdapter
from japarr.adapters.sonarr import SonarrAdapter
from japarr.adapters.radarr import RadarrAdapter
from japarr.adapters.discord import DiscordConnector
from japarr.db import JaparrDB
from japarr.adapters.jraws import JRawsDownloader
from japarr.logger import get_module_logger

from japarr.media_objects import Movie, Drama
from fastapi import FastAPI
import uvicorn
from queue import Queue
from threading import Thread
app = FastAPI()

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
        self.active = False
        self.logger = get_module_logger("DownloadManager")

    def _prepare_movie_obj(self, movie: Movie):
        media_obj = self.jraw_adapter.parse_media_details(movie.url)
        movie.set_media_details(media_obj)
        search_result = self.overseerr.search(media=movie, is_anime=False)
        if search_result:
            radarr_obj = self.radarr.create(search_result)
        return search_result, radarr_obj

    def _prepare_drama_obj(self, drama: Drama) -> Tuple[dict, dict]:
        media_obj = self.jraw_adapter.parse_media_details(drama.url)
        drama.set_media_details(media_obj)
        search_result = self.overseerr.search(media=drama, is_anime=False)
        if search_result:
            sonarr_obj = self.sonarr.create(search_result)
        return search_result, sonarr_obj

    def _save_movie_and_refresh(self, movie, radarr_obj):
        self.db.add_movie(movie.title, movie.url)
        if movie_id := radarr_obj.get("id"):
            result = self.radarr.refresh(movie_id)
            self.discord.send(
                f"Triggered autorefresh on {movie.title}: {result.get('message')}"
            )

    def _save_drama_and_refresh(self, episode: dict, sonarr_obj: dict):
        self.db.add_episode(
            episode["title"],
            episode["url"],
            episode["season"],
            episode["episode"],
            episode["ongoing"],
        )
        if episode_id := sonarr_obj.get("id"):
            result = self.sonarr.refresh(episode_id)
            self.discord.send(
                f"Triggered autorefresh on {episode.title}: {result.get('message')}"
            )

    def start_movies(self, page=1):
        movies, next_page = self.jraw_adapter.get_movies(page)
        for movie in movies:
            if not self.active:
                self.logger.info("Downloader paused. Stopping...")
                return
            if self.db.get_movie(movie.title):
                self.logger.info(
                    "Already downloaded %s, skipping!", movie.title
                )
                continue
            self.logger.debug("Searching for movie %s", movie.title)
            search_result, radarr_obj = self._prepare_movie_obj(movie)
            # if there is no metadata, we download the movie anyways
            if not search_result or radarr_obj["sizeOnDisk"] < 1:
                movie.folder = radarr_obj["folderName"]
                for _ in movie.download_files():
                    self._save_movie_and_refresh(movie, radarr_obj)
            else:
                self.logger.info(
                    f"Movie {movie.title} already exists, skipping download!"
                )
                self.db.add_movie(movie.title, movie.url)
        if next_page:
            self.start_movies(next_page)

    def start_dramas(self, page=1):
        dramas, next_page = self.jraw_adapter.get_dramas(page)
        for drama in dramas:
            if not self.active:
                self.logger.info("Downloader paused. Stopping...")
                return
            drama_entry = self.db.get_drama(drama.title)
            if drama_entry:
                if drama_entry[-1].ongoing == 0:
                    self.logger.info(
                        "Already fully downloaded %s, skippint!", drama.title
                    )
                    continue
                else:
                    self.logger.info(
                        "Drama %s exists, but is still ongoing!", drama.title
                    )
                    last_episode = drama[-1].episode
                    last_season = drama[-1].season
            self.logger.debug("Searching for drama %s", drama.title)
            search_result, sonarr_obj = self._prepare_drama_obj(drama)
            # if there is no metadata, we download the movie anyways
            if not search_result or sonarr_obj["sizeOnDisk"] < 1:
                drama.folder = sonarr_obj["folderName"]
                for episode in drama.download_files():
                    self._save_drama_and_refresh(episode, sonarr_obj)
            else:
                self.logger.info(
                    f"drama {drama.title} already exists, skipping download!"
                )
                self.db.add_drama(drama.title, drama.url)
        if next_page:
            self.start_dramas(next_page)

    def start_anime(self):
        """
        Still has to be implemented
        """
        pass

    def start(self):
        self.active = True
        self.start_movies()
        # self.start_dramas()
        # self.start_anime()

    def stop(self):
        self.active = False

dm = DownloadManager()

@app.post("/start")
def start_downloader():
    if not dm.active:
        p = Thread(target=dm.start)
        p.start()
        return {"status": "Started downloader!"}
    else:
        return {"status": "Downloader already running!"}

@app.post("/stop")
def start_downloader():
    if not dm.active:
        return {"status": "Downloader not running!"}
    else:
        p = Thread(target=dm.stop)
        p.start()
        return {"status": "Downloader stopped!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7557)