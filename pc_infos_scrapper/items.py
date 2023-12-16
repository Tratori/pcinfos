from scrapy.item import Item, Field

class CpuItem(Item):
    name = Field()
    physical = Field()
    processor = Field()
    performance = Field()
    architecture = Field()
    core = Field()
    cache = Field()
