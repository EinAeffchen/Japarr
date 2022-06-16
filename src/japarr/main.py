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
    def __init__(self) -> None:
        self.discord = DiscordConnector()
        self.sonarr = SonarrAdapter(self.discord)
        self.radarr = RadarrAdapter(self.discord)
        self.overseerr = OverseerAdapter()
        self.db = JaparrDB()
        self.jraw_adapter = JRawsDownloader

    def start(self):
        pass


if __name__ == "__main__":
    dm = DownloadManager()
    dm.start()
