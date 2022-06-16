import cgi
import re
import shutil
from typing import Generator, Optional, Tuple
import urllib.request
import requests
from parsel import Selector
from requests.compat import urljoin
from japarr.adapters.discord import DiscordConnector
from japarr.config.config import get_config
from japarr.media_objects import Movie
from requests import Response


class JRawsDownloader:
    BASE_URL: str
    DRAMA_URL: str
    MOVIE_URL: str

    def _load_config(self):
        cfg = get_config()
        self.DRAMA_PATH = cfg["general"]["dramas_path"]
        self.MOVIES_PATH = cfg["general"]["movies_path"]

    def __init__(self, discord: DiscordConnector):
        self._load_config()
        self.BASE_URL = "https://jraws.com/"
        self.DRAMA_URL = "https://jraws.com/category/drama/page/{}/"
        self.MOVIE_URL = "https://jraws.com/category/movie/page/{}/"
        self.discord = discord

    def _parse_articles(
        self, request: Response, article_type: str
    ) -> Tuple[int, list, Optional[str]]:
        sel = Selector(request.text)
        articles = sel.xpath("//article")
        article_list = list()
        for article in articles:
            article_dict = {}
            if article_type == "drama":
                article_dict["status"] = article.xpath(
                    "/div[@class='ep-date']/span[@class='ep-status-og']/text()"
                ).get()
            article_dict["drama_name"] = article.xpath(
                "/header/h2/a/text()"
            ).get()
            article_dict["eng_name"] = article.xpath(
                "/header/div[@class='ep-eng']/text()"
            ).get()
            article_dict["detail_url"] = article.xpath("//a/@href").get()
            article_list.append(article_dict)
        has_next_page = sel.xpath(
            "//nav/a[@class='next page-numbers']/@href"
        ).get()
        return article_list, has_next_page

    def get_movies(self, page: int = 1) -> Generator[Movie, None, None]:
        movie_page = requests.get(self.MOVIE_URL.format(page))
        article_list, has_next_page = self._parse_articles(
            movie_page, article_type="movie"
        )
        if has_next_page:
            yield self.get_movies(page + 1)
        yield article_list

    def _get_article_quality(self, content: str) -> Tuple[str, str, str]:
        content = content.replace("<code>", "").replace("</code>", "")
        quality, size, release = [info.strip() for info in content.split("|")]
        return quality, size, release

    def _parse_download(self, selector: Selector):
        download_links = selector.xpath("//a")
        downloads = dict()
        for download in download_links:
            episode = download.xpath("./span[@class='episode']/text()").get()
            url = download.xpath("./@href").get()
            downloads[episode] = url
        return downloads

    def parse_media_details(self, url: str, article_dict: dict) -> dict:
        response = requests.get(url)
        sel = Selector(response.text)
        article_dict["jap_title"] = sel.xpath("//h1/text()").getall()[1]
        download_infos = sel.xpath("//div[@id='download-list']/div")
        article_dict["quality"] = self._get_article_quality(
            download_infos.xpath("/text()").getall()[0]
        )
        article_dict["download_urls"] = self._parse_download(download_infos[1])
        return article_dict

    def download_episodes(self, drama_url: str):
        page_req = requests.get(drama_url)
        sel = Selector(page_req.text)

        episodes = sel.xpath("//div[@id='download-list']/div[2]/a").getall()
        show_title = sel.xpath("//h1/text()").getall()[0]
        show_title = "".join(
            [moji for moji in show_title if (moji.isalnum() or moji.isspace())]
        )

        folder = self.TARGET_PATH / show_title / "Season 01"
        folder.mkdir(exist_ok=True, parents=True)

        for i, episode in enumerate(episodes):
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
            if not (folder / filename).is_file():
                try:
                    with open(folder / filename, "wb") as f_in:
                        f_in.write(remotefile.read())
                except OverflowError:
                    with open(folder / filename, "wb") as f_in:
                        shutil.copyfileobj(remotefile, f_in, 4048 * 16192)
        return show_title

    def download_dramas_from_page(self, drama_page: requests.models.Request):
        next_page = sel.xpath(
            "//nav/span[contains(@class, 'current')]/following-sibling::a[1]/@href"
        ).get()
        if next_page:
            page = requests.get(next_page)
            self.download_dramas_from_page(page)
