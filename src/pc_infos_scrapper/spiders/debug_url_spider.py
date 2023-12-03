from pathlib import Path
import scrapy


class DebugSpider(scrapy.Spider):
    name = "debug"
    start_urls = ["https://www.techpowerup.com/cpu-specs/ryzen-3-5300g.c2473"]

    keys = ["Physical", "Processor", "Performance",
            "Architecture", "Core", "Cache"]

    def debug(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)

    def parse(self, response):
        def extract_with_css(query, selector=response):
            return selector.css(query).get(default="").strip()

        self.logger.critical("==================")

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
