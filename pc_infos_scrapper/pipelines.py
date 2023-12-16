import os
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from datetime import datetime

import constants
import csv
import json
import openpyxl


class CpuExportPipeline:
    def __init__(self) -> None:
        date_fmt = datetime.now().strftime("%Y%m%d")
        time_fmt = datetime.now().strftime("%H%M%S")

        # Defualt filename
        self.FILENAME = f"data/{date_fmt}_{time_fmt}_CPUS_OUT"

        dir_name = os.path.dirname(self.FILENAME)
        os.makedirs(
            dir_name, exist_ok=True
        )  # Create the directories if they don't exist

        # Unique ID for each CPU
        self._sequential = 1

        # .json
        self.json_file = None

        # .csv
        self.csv_file = None
        self.csv_writer = None

        # .xlsx
        self.workbook = None
        self.worksheet = None

    def open_spider(self, spider):
        # JSON initialization
        self.json_file = open(f"{self.FILENAME}.json", "w", encoding="utf-8")

        # CSV initialization
        self.csv_file = open(f"{self.FILENAME}.csv", "w", encoding="utf-8")
        self.csv_writer = csv.writer(
            self.csv_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        # Excel initialization
        # self.workbook = openpyxl.Workbook()
        # for key in constants.CPU_KEYS:
        #     self.workbook.create_sheet(key)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get("Name"):
            _flat_item = self._flatten_item(item)

            self._write_to_json(_flat_item)
            self._write_to_csv(_flat_item)

            self._sequential += 1
            return item
        else:
            raise DropItem(f"Item dropped: not scraped correctly.")

    def _flatten_item(self, data):
        _flattened_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                _flattened_data.update(value)
            else:
                _flattened_data[key] = value
        return _flattened_data

    def _write_to_csv(self, item):
        if self._sequential == 1:
            columns = list(item.keys())
            columns.insert(0, "ID")
            self.csv_writer.writerow(columns)
        data = list(item.values())
        data.insert(0, self._sequential)
        self.csv_writer.writerow(data)

    def _write_to_json(self, item):
        new_line = json.dumps({self._sequential: item})
        self.json_file.write(new_line)

    # def _write_to_excel(self, item):
    #     pass

    # def _write_to_xml(self, item):
    #     pass
