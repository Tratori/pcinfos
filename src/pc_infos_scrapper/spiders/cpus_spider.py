from pathlib import Path
import scrapy
from scrapy import signals
import time

KEYS = ["Physical", "Processor", "Performance", "Architecture", "Core", "Cache"]
MANUFACTURERS = ["AMD", "Intel"]
RELEASE_DATES = [str(i) for i in range(2023, 2015, -1)]

# MANUFACTURERS = ["AMD"]
# RELEASE_DATES = [2022]


class CPUSpider(scrapy.Spider):
    name = "cpus"
    base_url = "https://www.techpowerup.com/cpu-specs/?mfgr={0}&released={1}&mobile=No&server=No&sort=name"
    # handle_httpstatus_list = [302, 401, 404, 429]
    allowed_domains = ['www.techpowerup.com']

    custom_settings = {
        # 'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 5,
        'LOG_LEVEL': 'DEBUG',
        'TELNETCONSOLE_ENABLED': False,

        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_POLICY': 'pc_infos_scrapper.middlewares.CachePolicy',
        'COOKIES_ENABLED': False,

        'AUTOTHROTTLE_ENABLED': True,
        'AUTO_THROTTLE_DEBUG': True,
        
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,  # 400
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
            # 'pc_infos_scrapper.middlewares.PauseMiddleware': 999,
        },
        'DEFAULT_REQUEST_HEADERS': {
            "authority": "www.techpowerup.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
            "cookie": "_ga=GA1.2.350510651.1701566717; _gid=GA1.2.1468098798.1701566717; xffrom_search=google; xfcsrf=eo0ClSb7WJuUXYKW; botcheck=91630f101e7594c03c8196ba9a5933f7",
            "dnt": "1",
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        },

        # Extensions
        'ROTATING_PROXY_LIST_PATH': './src/pc_infos_scrapper/proxies.txt',
        'ROTATING_PROXY_PAGE_RETRY_TIMES': 20,

        'RANDOM_UA_PER_PROXY': True,
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

    def debug(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)

    def start_requests(self):
        for mfgr in MANUFACTURERS:
            for date in RELEASE_DATES:
                yield scrapy.Request(
                    url=self.base_url.format(mfgr, date), 
                    callback=self.parse,
                )

    def handle_spider_closed(self, reason):
        self.crawler.stats.set_value('failed_urls', ', '.join(self.failed_urls))


    def process_exception(self, response, exception, spider):
        ex_class = "%s.%s" % (exception.__class__.__module__, exception.__class__.__name__)
        self.crawler.stats.inc_value('downloader/exception_count', spider=spider)
        self.crawler.stats.inc_value('downloader/exception_type_count/%s' % ex_class, spider=spider)


    def parse(self, response):
        if not response.css('a.page-header__logo-wrapper'):
            # self.debug(response)
            yield scrapy.Request(url=response.url, )

        # if response.status in self.handle_httpstatus_list:
        #     self.crawler.stats.inc_value('failed_url_count')
        #     self.failed_urls.append(response.url)
        
        table = response.css('table.processors')
        rows = table.css('tr')

        # self.log(response)
        # self.log(response.status)
        # self.log(response.body)
        # self.log(table)
        # self.log(rows)
        # self.debug(response)

        for row in rows:
            follow_link = row.css('a::attr(href)').get()

            if follow_link is not None:
                yield response.follow(follow_link, callback=self.parse_cpu)

    def parse_cpu(self, response):

        # if response.status in [404, 429]:
        # if response.status in self.handle_httpstatus_list:
        #     self.crawler.stats.inc_value('failed_url_count')
        #     self.failed_urls.append(response.url)
        #     return

        # self.debug(response)

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

        self.log(processor['Name'])

        for key in KEYS:
            section = response.css(f'section:contains("{key}")')
            section_data = {}

            for tr in section.css("tr"):
                th = tr.css("th")
                td = tr.css("td")

                if th and td:
                    subkey = th.xpath(".//text()").get()
                    value = td.xpath(".//text()").get()

                    section_data[subkey.strip()] = value.strip() if value else ""

            processor[key] = section_data

        yield processor
