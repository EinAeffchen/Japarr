from typing import Optional

import requests
from japarr.adapters.base import BaseAdapter
from japarr.logger import get_module_logger
from japarr.media_objects import Movie
from requests import Response

logger = get_module_logger("Overseer")


class OverseerAdapter(BaseAdapter):
    search_keys: list
    # docs: https://api-docs.overseerr.dev/#/search/get_search
    def __init__(self):
        super().__init__("overseer")
        self.search_keys = ["original_title", "title", "english_title"]

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

    def _search_by_query(self, query: str, page:int =1) -> Optional[Response]:
        results = requests.get(
            f"{self.url}/v1/search?query=={query}&language=jp&page={page}",
            headers=self.headers,
        )
        if results.status_code != 200:
            logger.info("No results found for search: '%s'", query)
        else:
            results_json = results.json()
            if results_json.get("totalPages") > page:
                return results_json["results"] + self._search_by_query(query, page+1)
            return results_json["results"]

    def search(self, movie: Movie, is_anime=False) -> Optional[dict]:
        results = None
        key_index = 0
        while not results and key_index <= 2:
            query = getattr(movie, self.search_keys[key_index])
            if not query:
                key_index += 1
                continue
            results = self._search_by_query(query)
            key_index += 1
            for result in results:
                if self._is_japanese_and_exludes_genres(result, is_anime):
                    if result.get("mediaType") == "tv":
                        return self.get_tv_details(result["id"])
                    else:
                        return self.get_movie_details(result["id"])
                else:
                    results = None
            if not results:
                return

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
