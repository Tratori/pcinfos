from pathlib import Path
import scrapy


class CPUSpider(scrapy.Spider):
    name = "cpus"
    base_url = "https://www.techpowerup.com/cpu-specs/?mfgr={0}&released={1}&mobile=No&server=No&sort=name"
    manufacturers = ["AMD", "Intel"]
    release_date = [str(i) for i in range(2023, 1999, -1)]

    custom_settings = {
        'DOWNLOAD_DELAY': 10,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_DEBUG': True,
        'CONCURRENT_REQUESTS': 1,
        'COOKIES_ENABLED': False,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
            # 'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            # 'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
        },
        'HTTPCACHE_ENABLED': False,
        # 'ROTATING_PROXY_LIST_PATH': '.\\src\\pc_infos_scrapper\\proxies.txt',
        # 'LOG_LEVEL': 'INFO'
    }

    # release_date = [2021]
    # manufacturers = ["AMD"]

    keys = ["Physical", "Processor", "Performance",
            "Architecture", "Core", "Cache"]

    def debug(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)

    def response_is_ban(self, request, response):
        return b'banned' in response.body

    def exception_is_ban(self, request, exception):
        return None

    def start_requests(self):
        for mfgr in self.manufacturers:
            for date in self.release_date:
                yield scrapy.Request(url=self.base_url.format(mfgr, date), callback=self.parse)

    def parse(self, response):
        table = response.css('table.processors')
        rows = table.css('tr')

        for row in rows:
            follow_link = row.css('a::attr(href)').get()

            if follow_link is not None:
                yield response.follow(follow_link, callback=self.parse_cpu)

    def parse_cpu(self, response):
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

                    section_data[subkey.strip()] = value.strip() if value else ""

            processor[key] = section_data

        yield processor
