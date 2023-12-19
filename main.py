import logging

from scrapy.crawler import CrawlerProcess
from pc_infos_scrapper.spiders.cpus_spider import CpuSpider
from scrapy.utils.project import get_project_settings

from proxy_refresher import ProxyRefresher


def main():
    logging.basicConfig(
        level=logging.DEBUG,  # Set the root logger level
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()  # Output logs to the console
            # You can add more handlers if needed, such as logging to a file
        ],
    )

    logging.info("Starting main.py ...")

    # logging.info("Searching for proxy list ...")
    # refresher = ProxyRefresher()
    # if not refresher.file_is_updated():
    #     refresher.refresh_proxies()

    # os.environ["SCRAPY_SETTINGS_MODULE"] = "pc_infos_scrapper.settings"

    logging.info("Starting crawler ...")
    process = CrawlerProcess(get_project_settings())
    process.crawl(CpuSpider)
    process.start()  # the script will block here until the crawling is finished


if __name__ == "__main__":
    main()
