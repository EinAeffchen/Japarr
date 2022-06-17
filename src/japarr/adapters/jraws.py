from typing import Generator, List, Optional, Tuple, Union
import requests
from parsel import Selector
from japarr.logger import get_module_logger
from japarr.adapters.discord import DiscordConnector
from japarr.config.config import get_config
from japarr.media_objects import Drama, Movie
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
        self.logger = get_module_logger("JrawsDownloader")

    def _create_media_obj(
        self, article_type, status, title, detail_url, title_eng
    ) -> Union[Movie, Drama]:
        if article_type == "drama":
            if status.smaller() == "ongoing":
                ongoing = 1
            else:
                ongoing = 0
            media_obj = Drama(
                title=title,
                url=detail_url,
                status=ongoing,
                english_title=title_eng,
            )
        else:
            media_obj = Movie(
                title=title, url=detail_url, english_title=title_eng
            )
        return media_obj

    def _parse_articles(
        self, request: Response, article_type: str
    ) -> Tuple[List[Union[Movie, Drama]], Optional[str]]:
        sel = Selector(request.text)
        articles = sel.xpath("//article")
        article_list = list()
        self.logger.debug("Parsing %s articles", len(articles))
        for article in articles:
            title = article.xpath("./header/h2/a/text()").get()
            # english name is not always given
            title_eng = article.xpath(
                "./header/div[@class='ep-eng']/text()"
            ).get()
            detail_url = article.xpath(".//a/@href").get()
            status = article.xpath(
                "./div[@class='ep-date']/span[@class='ep-status-og']/text()"
            ).get()

            media_obj = self._create_media_obj(
                article_type, status, title, detail_url, title_eng
            )
            article_list.append(media_obj)
        has_next_page = sel.xpath(
            "//nav/a[@class='next page-numbers']/@href"
        ).get()
        return article_list, has_next_page

    def get_movies(self, page: int = 1) -> Tuple[List[Movie], int]:
        self.logger.debug("[*] Getting movies from page %s", page)
        movie_page = requests.get(self.MOVIE_URL.format(page))
        article_list, has_next_page = self._parse_articles(
            movie_page, article_type="movie"
        )
        if not has_next_page:
            return (article_list, 0)
        return (article_list, page+1)

    def _get_article_quality(self, content: str) -> Tuple[str, str, str]:
        quality, size, release = [info.strip() for info in content.split("|")]
        return quality, size, release

    def _parse_download(self, selector: Selector):
        download_links = selector.xpath("./a")
        downloads = dict()
        for download in download_links:
            episode = download.xpath("./span[@class='episode']/text()").get()
            url = download.xpath("./@href").get()
            downloads[episode] = f"https://jraws.com/{url}"
        return downloads

    def parse_media_details(self, url: str) -> dict:
        detail_dict = dict()
        response = requests.get(url)
        sel = Selector(response.text)
        detail_dict["jap_title"] = sel.xpath("//h1/text()").getall()[1]
        download_infos = sel.xpath("//div[@id='download-list']/div")
        meta_infos = download_infos.xpath("//code/text()").get()
        detail_dict["quality"] = self._get_article_quality(meta_infos)[0]
        detail_dict["download_urls"] = self._parse_download(download_infos[1])
        return detail_dict
