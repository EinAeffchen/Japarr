import cgi
import re
import shutil
import urllib.request
from pathlib import Path
from typing import List

import requests
from parsel import Selector

from japarr.config.config import get_config
from japarr.logger import get_module_logger


class MediaMetaObject:
    quality: str
    jap_title: str
    download_urls: List[dict]
    size: str
    release: str

    def __init__(self):
        pass

class Media:
    title: str
    url: str
    download_urls: dict
    original_title: str
    english_title: str
    quality: str
    folder: str

    def _get_file_path(self) -> Path:
        raise NotImplementedError

    def _extract_url(self, url: str) -> str:
        download_page = requests.get(url)
        sel = Selector(download_page.text)
        download_link_script = sel.xpath(
            "//script[contains(text(), 'video-downloads')]/text()"
        ).get()
        try:
            download_link = re.search(
                r"https:\/\/video-downloads\.googleusercontent\.com\/[\w-]+",
                download_link_script,
            ).group(0)
        except TypeError:
            print(download_link)
        return download_link

    def _check_folder(self) -> Path:
        path = self._get_file_path()
        if not path.is_dir():
            path.mkdir(exist_ok=True, parents=True)
        return path

    def _download(self, download_link: str, path: Path, episode: int):
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
        disposition = remotefile.info()["Content-Disposition"]
        value, params = cgi.parse_header(disposition)
        if isinstance(self, Drama):
            filename = params["filename"].replace("EP", "S01EP")
            filename = filename.replace("ep", f"S0{self.season}EP")
            filename = filename.replace("Ep", f"S0{self.season}EP")
        else:
            filename = params["filename"]
        if not (path / filename).is_file():
            with requests.get(download_link, stream=True) as r:
                with open(path / filename, "wb") as f_in:
                    for chunk in r.iter_content(chunk_size=4048 * 16192):
                        f_in.write(chunk)
        if isinstance(self, Drama):
            return {
                "title": self.title,
                "episode": episode,
                "season": self.season,
            }
        else:
            return {"title": self.title}

    def download_files(self):
        path = self._check_folder()
        for episode, url in self.download_urls.items():
            download_link = self._extract_url(url)
            yield self._download(download_link, path, episode)

    def set_media_details(self, media_obj: MediaMetaObject):
        self.original_title = media_obj.jap_title
        self.quality = media_obj.quality
        self.download_urls = media_obj.download_urls

    def __init__(
        self,
        title: str,
        url: str,
        download_urls: list = None,
        original_title: str = None,
        english_title: str = None,
        quality: str = None,
    ) -> None:
        self.title = title
        self.url = url
        self.download_urls = download_urls
        self.original_title = original_title
        self.english_title = english_title
        self.quality = quality
        self.logger = get_module_logger("Media")


class Movie(Media):
    def _get_file_path(self) -> str:
        cfg = get_config()
        movie_path = Path(cfg["general"]["movies_path"])
        return movie_path / Path(self.folder).name

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.logger = get_module_logger("Movie")


class Drama(Media):
    season: int
    ongoing: int

    def _get_file_path(self) -> str:
        cfg = get_config()
        movie_path = Path(cfg["general"]["movies_path"])
        return movie_path / f"Season {self.season}" / self.title

    def __init__(
        self,
        season: int = None,
        ongoing: int = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.season = season
        self.ongoing = ongoing
        self.logger = get_module_logger("Drama")