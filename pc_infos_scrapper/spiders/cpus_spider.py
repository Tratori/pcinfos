from pathlib import Path
import scrapy
from scrapy import signals
import os
import time

import constants
from pc_infos_scrapper.items import CpuItem


# Techpowerup CPU specs page
BASE_URL = "https://www.techpowerup.com/cpu-specs/?mfgr={0}&released={1}&mobile=No&server=Yes&sort=name"
TEST_CPU_URL_SINGLE = ""

# List of CPU manufacturers
MANUFACTURERS = ["AMD"]
RELEASE_DATES = [str(i) for i in range(2003, 2025, 1)]


class CpuSpider(scrapy.Spider):
    name = "cpus"
    allowed_domains = ["www.techpowerup.com"]
    urls = [
        BASE_URL.format(mnfr, date) for mnfr in MANUFACTURERS for date in RELEASE_DATES
    ]

    handle_httpstatus_list = [302, 401, 403, 404, 429]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_urls = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CpuSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def start_requests(self):
        if TEST_CPU_URL_SINGLE:
            yield scrapy.Request(url=TEST_CPU_URL_SINGLE, callback=self.parse_cpu)
        else:
            for url in self.urls:
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Logo check
        # if not response.css('a.page-header__logo-wrapper'):
        #     yield scrapy.Request(url=response.url, )

        # handle http errors
        if response.status in self.handle_httpstatus_list:
            if response.status == 429:
                print(f"Received 429 Too Many Requests for URL: {response.url}")
                print("Please fix the issue, then press Enter to retry...")
                input()  # Wait for manual intervention
                yield scrapy.Request(
                    url=response.url, callback=self.parse, dont_filter=True
                )
                return
            self.process_exception(response, str(response.status), self)
            return

        table = response.css("table.processors")
        rows = table.css("tr")

        for row in rows:
            follow_link = row.css("a::attr(href)").get()

            if follow_link is not None:
                yield response.follow(follow_link, callback=self.parse_cpu)

        # if not rows and response.status == 200:
        #     self.debug(response)

    def parse_cpu(self, response):
        # handle http errors
        if response.status in self.handle_httpstatus_list:
            if response.status == 429:
                print(f"Received 429 Too Many Requests for URL: {response.url}")
                print("Please fix the issue, then press Enter to retry...")
                input()  # Wait for manual intervention
                yield scrapy.Request(
                    url=response.url, callback=self.parse_cpu, dont_filter=True
                )
                return
            self.process_exception(response, str(response.status), self)
            return

        def extract_with_css(query, selector=response):
            return selector.css(query).get(default="").strip()

        # Get <section> tag which contains
        # nested <h1> tags with following texts:
        # - "Physical"
        # - "Processor"
        # - "Performance"
        # - "Architecture"
        # - "Core"
        # - "Cache"

        processor = {}
        cpu = CpuItem()

        cpu["name"] = extract_with_css("h1.cpuname::text")
        processor["Name"] = extract_with_css("h1.cpuname::text")

        for key in constants.CPU_KEYS:
            section = response.css(f'section:contains("{key}")')
            section_data = {}

            for tr in section.css("tr"):
                th = tr.css("th::text")
                td = tr.css("td::text")

                if th and td:
                    subkey = th.get()
                    value = td.get()

                    section_data[subkey.strip().replace(":", "")] = (
                        value.strip() if value else ""
                    )

            processor[key] = section_data
            cpu[key.lower()] = section_data

        # Features parsing
        section = response.css(f'section:contains("Features")')
        feature_list = []
        for tr in section.css("tr"):
            for li in tr.css("li"):
                feature = li.css("::text").get()
                if feature:
                    feature_list.append(feature.strip())
        print(f"Feature list: {feature_list}")
        processor["features"] = {"tags": feature_list}
        cpu["features"] = {"tags": feature_list}
        yield processor

    def process_exception(self, response, exception, spider):
        ex_class = "%s.%s" % (
            exception.__class__.__module__,
            exception.__class__.__name__,
        )
        self.crawler.stats.inc_value("downloader/exception_count", spider=spider)
        self.crawler.stats.inc_value(
            "downloader/exception_type_count/%s" % ex_class, spider=spider
        )

        # throw url in failed_urls list:
        if response.url not in self.failed_urls:
            self.failed_urls.append(response.url)

    def spider_closed(self, reason):
        self.crawler.stats.set_value("failed_urls", ", ".join(self.failed_urls))

    def debug(self, response):
        from scrapy.shell import inspect_response

        inspect_response(response, self)
