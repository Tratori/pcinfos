
import os
from scrapy.crawler import CrawlerProcess
from pc_infos_scrapper.spiders.cpus_spider import CPUSpider
from scrapy.utils.project import get_project_settings


def main():

    # TODO: update proxy file if 
    # 1) it doesn't exist
    # 2) it's older than 1 day
    # 3) it's empty, it's invalid or it's not a list of proxies


    os.environ['SCRAPY_SETTINGS_MODULE'] = 'pc_infos_scrapper.settings'
    # os.environ['SCRAPY_PROJECT'] = 'default'

    process = CrawlerProcess(
        get_project_settings()
    )

    process.crawl(CPUSpider)
    process.start()  # the script will block here until the crawling is finished


if __name__ == "__main__":
    main()
