from pathlib import Path
import scrapy
from scrapy import signals
import time


class CPUSpider(scrapy.Spider):
    name = "cpus"
    base_url = "https://www.techpowerup.com/cpu-specs/?mfgr={0}&released={1}&mobile=No&server=No&sort=name"
    manufacturers = ["AMD", "Intel"]
    release_date = [str(i) for i in range(2023, 1999, -1)]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 15,
        'DEFAULT_REQUEST_HEADERS': {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        },
        'DOWNLOADER_MIDDLEWARES': {
            'pc_infos_scrapper.middlewares.PauseMiddleware': 999,
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_DEBUG': True,
        'HTTPCACHE_ENABLED': True,
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'cpus.log',
    }

    # Append all failed urls in a list to retry them separately later
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_urls = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CPUSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.handle_spider_closed, signals.spider_closed)
        return spider

    keys = ["Physical", "Processor", "Performance",
            "Architecture", "Core", "Cache"]

    def debug(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)

    def start_requests(self):
        for mfgr in self.manufacturers:
            for date in self.release_date:
                yield scrapy.Request(url=self.base_url.format(mfgr, date), callback=self.parse)

    def handle_spider_closed(self, reason):
        self.crawler.stats.set_value('failed_urls', ', '.join(self.failed_urls))

    def process_exception(self, response, exception, spider):
        ex_class = "%s.%s" % (exception.__class__.__module__, exception.__class__.__name__)
        self.crawler.stats.inc_value('downloader/exception_count', spider=spider)
        self.crawler.stats.inc_value('downloader/exception_type_count/%s' % ex_class, spider=spider)


    def parse(self, response):
        table = response.css('table.processors')
        rows = table.css('tr')

        for row in rows:
            follow_link = row.css('a::attr(href)').get()

            if follow_link is not None:
                yield response.follow(follow_link, callback=self.parse_cpu)

    def parse_cpu(self, response):

        # if response.status in [404, 429]:
        if response.status != 200:
            self.crawler.stats.inc_value('failed_url_count')
            self.failed_urls.append(response.url)

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
        processor['Name'] = extract_with_css("h1.cpuname::text")

        for key in self.keys:
            section = response.css(f'section:contains("{key}")')
            section_data = {}

            for tr in section.css("tr"):
                th = tr.css("th")
                td = tr.css("td")

                if th and td:
                    subkey = th.xpath(".//text()").get()
                    value = td.xpath(".//text()").get()

                    section_data[subkey.strip()] = value.strip(
                    ) if value else ""

            processor[key] = section_data

        yield processor
