import scrapy
from scrapy.crawler import CrawlerProcess

from pc_infos_scrapper.spiders.cpus_spider import CPUSpider


def main():
    process = CrawlerProcess(
        settings={
            "FEEDS": {
                "items.json": {"format": "json"},
            },
        }
    )

    process.crawl(CPUSpider)
    process.start()  # the script will block here until the crawling is finished

if __name__ == "__main__":
    main()
