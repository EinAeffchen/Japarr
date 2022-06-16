from typing import List


class Media:
    title: str
    url: str
    download_url: str
    original_title: str
    english_title: str
    download_urls: str
    quality: str

    def _get_file_path(self) -> str:
        pass

    def download_episodes(self):
        pass

    def set_media_details(self, detail_dict):
        self.original_title = detail_dict["original_title"]
        self.quality = detail_dict["quality"]
        self.download_urls = detail_dict["download_urls"]

    def __init__(
        self,
        title: str,
        url: str,
        download_urls: str=None,
        original_title: str=None,
        english_title: str = None,
        quality: str=None
    ) -> None:
        self.title = title
        self.url = url
        self.download_urls = download_urls
        self.original_title = original_title
        self.english_title = english_title
        self.quality = quality


class Movie(Media):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class Drama(Media):
    episode: int
    season: int
    ongoing: int
    download_urls: List[str]

    def __init__(
        self,
        episode: int = None,
        season: int = None,
        ongoing: int = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.episode = episode
        self.season = season
        self.ongoing = ongoing
