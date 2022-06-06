from typing import Optional

import requests
from japarr.adapters.base import BaseAdapter
from japarr.logger import get_module_logger

logger = get_module_logger("Overseer")


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
                if (
                    "JP" in result.get("originCountry", [])
                    or result.get("originalLanguage", "") == "ja"
                ):
                    if result.get("mediaType") == "tv":
                        return self.get_tv_details(result["id"])
                    else:
                        return self.get_movie_details(result["id"])
        else:
            logger.info("No results found for search: '%s'", query)

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
