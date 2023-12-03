from pathlib import Path
from ..utils.table import Table

import scrapy


class CPUSSpider(scrapy.Spider):
    name = "cpus"
    start_urls = ["https://www.techpowerup.com/cpu-specs/"]

    keys = [ "Physical", "Processor", "Performance", "Architecture", "Core", "Cache" ]

    def debug(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response, self)

    def parse(self, response):
        page = response.body

        table = response.css('table.processors')
        rows = table.css('tr')

        for row in rows:
            follow_link = row.css('a::attr(href)').get()

            if follow_link is not None:
                yield response.follow(follow_link, callback=self.parse_cpu)

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)

        # table = Table(response.css('table.processors'))
        # print(table.get_rows()[3])

    def parse_cpu(self, response):

        # proxy check
        if not response.css("a.page-header__logo"):
            yield response.Request(url=response.url, dont_filter=True)

        def extract_with_css(query, selector=response):
            return selector.css(query).get(default="").strip()

        def extract_nested_td(selector, td_index):
            return selector.css("tr")[td_index].css("td").xpath(".//text()").get().strip()

        def extract_nested_td_with_contains(selector, contains_txt):
            return selector.css(f"tr:contains('{contains_txt}')").css("td").xpath(".//text()").get().strip()

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

        # physical = response.css('section:contains("Physical")')
        # processor = response.css('section:contains("Processor")')
        # performance = response.css('section:contains("Performance")')
        # core = response.css('section:contains("Core")')
        # cache = response.css('section:contains("Cache")')
        # architecture = response.css('section:contains("Architecture")')

        # self.debug(response)

        # yield {
        #     "Name": extract_with_css("h1.cpuname::text"),
        #     "Physical": {
        #         "socket": extract_nested_td(physical, 0),
        #         "foundry": extract_nested_td(physical, 1),
        #         "process_size": extract_nested_td(physical, 2),
        #         "transistors": extract_nested_td(physical, 3),
        #         "die_size": extract_nested_td(physical, 4),
        #         "io_process_size": extract_nested_td(physical, 5),
        #         "io_die_size": extract_nested_td(physical, 6),
        #         "package": extract_nested_td(physical, 7),
        #         "t_case_max": extract_nested_td(physical, 8),
        #     },
        #     "Processor": {
        #         "market": extract_nested_td(processor, 0),
        #         "production_status": extract_nested_td(processor, 1),
        #         "release_date": extract_nested_td(processor, 2),
        #         "launch_price": extract_nested_td(processor, 3),
        #         "part_no": extract_nested_td(processor, 4),
        #         "bundled_cooler": extract_nested_td(processor, 5)
        #     },
        #     "Performance": {
        #         "frequency": extract_nested_td(performance, 0),
        #         "turbo_clock": extract_nested_td(performance, 1),
        #         "base_clock": extract_nested_td(performance, 2),
        #         "multiplier": extract_nested_td(performance, 3),
        #         "multiplier_unlocked": extract_nested_td(performance, 4),
        #         "tdp": extract_nested_td(performance, 5),
        #         "fp32": extract_nested_td(performance, 6),
        #     },
        #     "Architecture": {
        #         "codename": extract_nested_td(architecture, 0),
        #         "generation": extract_nested_td(architecture, 1),
        #         "memory_support": extract_nested_td(architecture, 2),
        #         "rated_speed": extract_nested_td(architecture, 3),
        #         "memory_bus": extract_nested_td(architecture, 4),
        #         "ecc_memory": extract_nested_td(architecture, 5),
        #         "pci_express": extract_nested_td(architecture, 6),
        #         "chipsets": extract_nested_td(architecture, 7)
        #     },
        #     "Core": {
        #         "no_cores": extract_nested_td(core, 0),
        #         "no_threads": extract_nested_td(core, 1),
        #         "smp_no_cpus": extract_nested_td(core, 2),
        #         "integrated_graphics": extract_nested_td(core, 3),
        #     },
        #     "Cache": {
        #         "L1": extract_nested_td(cache, 0),
        #         "L2": extract_nested_td(cache, 1),
        #         "L3": extract_nested_td(cache, 2)
        #     },
        # }
