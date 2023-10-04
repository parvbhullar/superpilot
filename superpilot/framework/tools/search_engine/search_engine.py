#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from superpilot.core.configuration import get_config, Config

from .search_engine_serper import SerperWrapper
from .search_engine_serpapi import SerpAPIWrapper
from .search_engine_type import SearchEngineType

config: Config = get_config()


class SearchEngine:
    """ """

    def __init__(self, config, engine=None, run_func=None):
        self.config = config
        self.run_func = run_func
        self.engine = (
            engine or SearchEngineType.DIRECT_GOOGLE or self.config.search_engine
        )

    def run_google(self, query, max_results=8, **kwargs):
        # results = ddg(query, max_results=max_results)
        results = self.google_official_search(query, num_results=max_results, **kwargs)
        # logger.info(results)
        return results

    async def run(self, query: str, max_results=8, **kwargs):
        if self.engine == SearchEngineType.SERPAPI_GOOGLE:
            api = SerpAPIWrapper(config.serp_api_key)
            rsp = await api.run(query, **kwargs)
        elif self.engine == SearchEngineType.DIRECT_GOOGLE:
            rsp = self.run_google(query, max_results, **kwargs)
        elif self.engine == SearchEngineType.SERPER_GOOGLE:
            api = SerperWrapper()
            rsp = await api.run(query, **kwargs)
        elif self.engine == SearchEngineType.CUSTOM_ENGINE:
            rsp = self.run_func(query, **kwargs)
        else:
            raise NotImplementedError
        return rsp

    def google_official_search(
        self,
        query: str,
        num_results: int = 8,
        focus=["snippet", "link", "title"],
        **kwargs,
    ) -> dict | list[dict]:
        """Return the results of a Google search using the official Google API

        Args:
            query (str): The search query.
            num_results (int): The number of results to return.

        Returns:
            str: The results of the search.
        """

        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        try:
            api_key = self.config.google_api_key
            custom_search_engine_id = self.config.google_custom_search_engine_id
            print(self.config)
            with build("customsearch", "v1", developerKey=api_key) as service:
                result = (
                    service.cse()
                    .list(
                        q=query,
                        cx=custom_search_engine_id,
                        num=num_results,
                        **kwargs,
                    )
                    .execute()
                )
                # logger.info(result)
                # Extract the search result items from the response
            search_results = result.get("items", [])
            # print(search_results)
            # Create a list of only the URLs from the search results
            search_results_details = [
                {i: j for i, j in item_dict.items() if i in focus}
                for item_dict in search_results
            ]

        except HttpError as e:
            # Handle errors in the API call
            error_details = json.loads(e.content.decode())

            # Check if the error is related to an invalid or missing API key
            if error_details.get("error", {}).get(
                "code"
            ) == 403 and "invalid API key" in error_details.get("error", {}).get(
                "message", ""
            ):
                return "Error: The provided Google API key is invalid or missing."
            else:
                return f"Error: {e}"
        # google_result can be a list or a string depending on the search results

        # Return the list of search result URLs
        return search_results_details

    def safe_google_results(self, results: str | list) -> str:
        """
            Return the results of a google search in a safe format.

        Args:
            results (str | list): The search results.

        Returns:
            str: The results of the search.
        """
        if isinstance(results, list):
            safe_message = json.dumps(
                # FIXME: # .encode("utf-8", "ignore") 这里去掉了，但是AutoGPT里有，很奇怪
                [result for result in results]
            )
        else:
            safe_message = results.encode("utf-8", "ignore").decode("utf-8")
        return safe_message


if __name__ == "__main__":
    SearchEngine.run(query="wtf")
