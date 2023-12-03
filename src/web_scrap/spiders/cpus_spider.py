from pathlib import Path
from ..utils.table import Table

import scrapy


class CPUSpider(scrapy.Spider):
    name = "cpus"
    base_url = "https://www.techpowerup.com/cpu-specs/?mfgr={0}&released={1}&mobile=No&server=No&sort=name"
    manufacturers = ["AMD", "Intel"]
    release_date = [str(i) for i in range(2023, 1999, -1)]
    
    # release_date = [2021]
    
    keys = [ "Physical", "Processor", "Performance", "Architecture", "Core", "Cache" ]

    def debug(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)
    
    def start_requests(self):
        urls = []

        for mfgr in self.manufacturers:
            for date in self.release_date:
                urls.append(self.base_url.format(mfgr, date))

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        page = response.body

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
            sectionData = {}

            for tr in section.css("tr"):
                th = tr.css("th")
                td = tr.css("td")
                # print("===========tr===========")
                # print(th.xpath(".//text()").get().strip(), td.xpath(".//text()").get().strip())
                
                if th and td:
                    sectionData[th.xpath(".//text()").get().strip()] = td.xpath(".//text()").get().strip()

            processor[key] = sectionData

        yield processor
