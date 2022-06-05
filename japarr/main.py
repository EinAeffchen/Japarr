#!/usr/bin/env python
# coding: utf-8


import cgi
import json
from lib2to3.pytree import Base
from mimetypes import init
import re
import shutil
from typing import Optional
from unittest import result
import urllib.request
from distutils.command.config import config
from pathlib import Path

import requests
import toml
from parsel import Selector
from requests.compat import quote_plus, urljoin
from tqdm import tqdm

from japarr.logger import get_module_logger

logger = get_module_logger("Japarr")


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
                    return result
        else:
            print(results.status_code)


class SonarrAdapter(BaseAdapter):
    # docs: https://github.com/Sonarr/Sonarr/wiki/Series
    def __init__(self):
        super().__init__("sonarr")

    def create(self, overseer_data: dict) -> dict:
        media_info = overseer_data["mediaInfo"]
        data = {
            "tvdbId": media_info["tvdbId"],
            "title": overseer_data["name"],
            "profileId": 0,
            "titleSlug": overseer_data["name"],
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
            "seasons": [],  # TODO
        }
        requests.post(f"{self.url}/series", data=data, headers=self.headers)


class RadarrAdapter(BaseAdapter):
    def __init__(self):
        super().__init__("radarr")


class JRawsDownloader:
    BASE_URL = "https://jraws.com/"
    DRAMA_URL = "https://jraws.com/category/drama/"
    TARGET_PATH = Path("O:/tvshows/shows")
    SAVE_PATH = Path("./jraw_cache")
    SAVE_PATH.mkdir(exist_ok=True, parents=True)
    SAVE_FILE = "save_data.json"
    downloaded_dramas = []
    page = None

    def __init__(self):
        self.load_SAVE_PATH()
        if self.page and int(self.page) > 1:
            self.DRAMA_URL += f"page/{self.page}/"
        drama_page = requests.get(self.DRAMA_URL)
        self.download_dramas_from_page(drama_page)

    def download_all_episodes(self, drama_url: str):
        page_req = requests.get(drama_url)
        sel = Selector(page_req.text)

        episodes = sel.xpath("//div[@id='download-list']/div[2]/a").getall()
        show_title = sel.xpath("//h1/text()").getall()[0]
        show_title = "".join(
            [moji for moji in show_title if (moji.isalnum() or moji.isspace())]
        )

        if show_title in self.downloaded_dramas:
            return
        folder = self.TARGET_PATH / show_title / "Season 01"
        folder.mkdir(exist_ok=True, parents=True)

        for i, episode in tqdm(enumerate(episodes)):
            episode_page_url = urljoin(self.BASE_URL, episode)
            episode_page = requests.get(episode_page_url)
            new_sel = Selector(episode_page.text)
            download_link_script = new_sel.xpath(
                "//script[contains(text(), 'video-downloads')]/text()"
            ).get()
            try:
                download_link = re.search(
                    r"https:\/\/video-downloads\.googleusercontent\.com\/[\w-]+",
                    download_link_script,
                ).group(0)
            except TypeError:
                print(download_link)
            opener = urllib.request.build_opener()
            opener.addheaders = [
                ("Host", "video-downloads.googleusercontent.com"),
                (
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
                ),
                (
                    "Accept",
                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                ),
                ("Accept-Language", "en-US,en;q=0.5"),
                ("Accept-Encoding", "gzip, deflate, br"),
                ("Connection", "keep-alive"),
                ("Referer", "https://jraws.com/"),
                ("Upgrade-Insecure-Requests", "1"),
                ("Sec-Fetch-Dest", "document"),
                ("Sec-Fetch-Mode", "navigate"),
                ("Sec-Fetch-Site", "cross-site"),
                ("Sec-Fetch-User", "?1"),
            ]
            urllib.request.install_opener(opener)
            remotefile = urllib.request.urlopen(download_link)
            blah = remotefile.info()["Content-Disposition"]
            value, params = cgi.parse_header(blah)
            filename = params["filename"].replace("EP", "S01EP")
            filename = filename.replace("ep", "S01EP")
            filename = filename.replace("Ep", "S01EP")
            print(f"Downloading {filename}...")
            # urllib.request.urlretrieve(download_link, folder / filename)
            if not (folder / filename).is_file():
                try:
                    with open(folder / filename, "wb") as f_in:
                        f_in.write(remotefile.read())
                except OverflowError:
                    with open(folder / filename, "wb") as f_in:
                        shutil.copyfileobj(remotefile, f_in, 4048 * 16192)
        return show_title

    def save_state(self, show_title: str, page_number: str):
        self.downloaded_dramas.append(show_title)
        with open(self.SAVE_PATH / self.SAVE_FILE, "w") as f_out:
            json.dump(
                {"page": page_number, "dramas": self.downloaded_dramas}, f_out
            )

    def download_dramas_from_page(self, drama_page: requests.models.Request):
        sel = Selector(drama_page.text)
        dramas = sel.xpath("//article/div/a/@href").getall()
        page_number = drama_page.url.split("/")[-2]
        if not page_number.isdigit():
            page_number = 1
        for drama in dramas:
            show_title = self.download_all_episodes(drama)
            self.save_state(show_title, page_number)
        next_page = sel.xpath(
            "//nav/span[contains(@class, 'current')]/following-sibling::a[1]/@href"
        ).get()
        if next_page:
            page = requests.get(next_page)
            self.download_dramas_from_page(page)

    def load_SAVE_PATH(self):
        if (self.SAVE_PATH / self.SAVE_FILE).is_file():
            with open(self.SAVE_PATH / self.SAVE_FILE, "r") as f_in:
                save_file = json.load(f_in)
                self.page = save_file["page"]
                self.downloaded_dramas = save_file["dramas"]


if __name__ == "__main__":
    overseer = OverseerAdapter()
    overseer.search("シジュウカラ")
