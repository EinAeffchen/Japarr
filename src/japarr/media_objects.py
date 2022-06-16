from typing import List

class Media:
    title: str
    url: str
    download_url: str

    def __init__(self, title: str, url: str) -> None:
        self.title = title
        self.url = url

class Movie(Media):
    def __init__(self, title: str, url: str) -> None:
        super().__init__(title, url)

class Drama(Media):
    episode: int
    season: int
    ongoing: int
    episode_urls: List[str]

    def __init__(self, title: str, url: str, episode: int, season: int, ongoing: int) -> None:
        super().__init__(title, url)
        self.episode = episode
        self.season = season
        self.ongoing = ongoing
