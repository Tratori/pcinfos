from pathlib import Path
from ..utils.table import Table

import scrapy


class CPUSSpider(scrapy.Spider):
    name = "cpus"
    start_urls = [ "https://www.techpowerup.com/cpu-specs/" ]

    def parse(self, response):
        page = response.body

        table = response.css('table.processors')
        rows = table.css('tr')

        for row in rows:
            follow_link = row.css('a::attr(href)').get()
            print(follow_link)

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        # table = Table(response.css('table.processors'))
        # print(table.get_rows()[3])



















