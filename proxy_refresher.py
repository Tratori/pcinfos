import os
import re
import time
import constants
import requests
import logging


class ProxyRefresher:
    def __init__(self) -> None:
        self._file_is_updated = False
        self._proxies = []
        self._checked_proxies = []

    def file_is_updated(self) -> bool:
        if not os.path.isfile(constants.PROXY_LIST_LOCAL_FILENAME):
            logging.info("No proxy list found, creating one ...")
            return self._file_is_updated

        _DAY = 86400
        _N_DAYS = 0.5

        if (
            os.path.getctime(constants.PROXY_LIST_LOCAL_FILENAME)
            > time.time() - _DAY * _N_DAYS
        ):
            self._file_is_updated = True
        else:
            logging.info("Proxy list is outdated, refreshing ...")

        return self._file_is_updated

    def refresh_proxies(self) -> None:
        self._call_proxy_urls(constants.PROXY_LIST_WEB_SOURCES)
        self._test_proxies()
        self._dump_proxy_file(constants.PROXY_LIST_LOCAL_FILENAME)

    def _call_proxy_urls(self, urls: list) -> list:
        ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b")

        for url in urls:
            response = requests.get(url)

            if response.status_code != 200:
                logging.error(
                    f"Error while getting proxy list from {url} : {response.status_code}"
                )
                continue

            content_lines = response.text.splitlines()
            for line in content_lines:
                match = ip_pattern.search(line)
                if match:
                    ip_address = match.group()
                    self._proxies.append(ip_address)

        return self._proxies

    def _test_proxies(self) -> list:
        logging.info("Testing proxies ...")

        for _ in self._proxies:
            proxy = self._proxies.pop()

            try:
                response = requests.get(
                    constants.PROXY_TEST_URL,
                    proxies={"http": proxy, "https": proxy},
                    timeout=constants.PROXY_TEST_TIMEOUT,
                )
                if response.status_code == 200:
                    self._checked_proxies.append(proxy)
            except requests.exceptions.RequestException:
                continue

        return self._checked_proxies

    def _dump_proxy_file(self, filename) -> None:
        directory = os.path.dirname(filename)

        if not os.path.exists(directory):
            os.makedirs(directory)

        # Write the list to the file
        with open(filename, "w") as file:
            for item in self._checked_proxies:
                file.write(item + "\n")
