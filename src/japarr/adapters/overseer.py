from typing import Optional

import requests
from japarr.adapters.base import BaseAdapter
from japarr.logger import get_module_logger

logger = get_module_logger("Overseer")


class OverseerAdapter(BaseAdapter):
    # docs: https://api-docs.overseerr.dev/#/search/get_search
    def __init__(self):
        super().__init__("overseer")

    @staticmethod
    def _is_japanese_and_exludes_genres(result: dict, is_anime: bool) -> bool:
        if not is_anime:
            exclude_genres = [16]
        else:
            exclude_genres = []
        if (
            "JP" in result.get("originCountry", [])
            or result.get("originalLanguage", "") == "ja"
        ) and not any(
            [genre_id in result.get("genreIds") for genre_id in exclude_genres]
        ):
            return True

    def search(self, query: str, is_anime=False) -> Optional[dict]:
        results = requests.get(
            f"{self.url}/v1/search?query=={query}&language=jp",
            headers=self.headers,
        )
        if results.status_code != 200:
            logger.info("No results found for search: '%s'", query)
            return

        result_json = results.json()
        for result in result_json.get("results", []):
            if self._is_japanese_and_exludes_genres(result, is_anime):
                if result.get("mediaType") == "tv":
                    return self.get_tv_details(result["id"])
                else:
                    return self.get_movie_details(result["id"])

    def get_tv_details(self, id: int):
        results = requests.get(
            f"{self.url}/v1/tv/{id}",
            headers=self.headers,
        )
        if results.status_code == 200:
            return results.json()
        else:
            logger.info("Couldn't find details to tvshow id: %s", id)

    def get_movie_details(self, id: int):
        results = requests.get(
            f"{self.url}/v1/movie/{id}",
            headers=self.headers,
        )
        if results.status_code == 200:
            return results.json()
        else:
            logger.info("Couldn't find details to movie id: %s", id)
