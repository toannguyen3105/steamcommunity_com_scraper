# -*- coding: utf-8 -*-
import csv
import glob
import os.path
from openpyxl import Workbook
import urllib.parse as urlparse
from urllib.parse import parse_qs

from scrapy.spiders import Spider
from scrapy.http import Request
from scrapy.exceptions import CloseSpider

CSGO_APP_ID = 730
DOTA2_APP_ID = 570
CSGO_MIN_PRICE = 20
DOTA2_MIN_PRICE = 10
COUNT = 100
CURRENCY_BASE_DEVIDE = 100


class ItemSpider(Spider):
    name = 'item'
    allowed_domains = ['steamcommunity.com']
    start_urls = ['http://steamcommunity.com/']

    def __init__(self, app_id=None):
        self.app_id = app_id

    def parse(self, response):
        yield Request(
            f'https://steamcommunity.com/market/search/render/?query=&start=0&search_descriptions=0&sort_column=price&sort_dir=desc&count={COUNT}&appid=' + self.app_id + '&norender=1',
            callback=self.parse_item)

    def parse_item(self, response):
        if response.text != "":
            resJson = response.json()
            results = resJson["results"]

            for item in results:
                if int(self.app_id) == CSGO_APP_ID and item["sell_price"] / CURRENCY_BASE_DEVIDE < CSGO_MIN_PRICE:
                    raise CloseSpider('CSGO is reach min price')
                elif int(self.app_id) == DOTA2_APP_ID and item["sell_price"] / CURRENCY_BASE_DEVIDE < DOTA2_MIN_PRICE:
                    raise CloseSpider('DOTA2 is reach min price')
                else:
                    yield {
                        "name": item["name"],
                        "quantity": item["sell_listings"],
                        "price": item["sell_price"] / CURRENCY_BASE_DEVIDE,
                    }

            start = resJson['start']
            total_count = resJson['total_count']
            if start + COUNT < total_count:
                yield Request(response.urljoin(
                    f'?query=&start={start + COUNT}&search_descriptions=0&sort_column=price&sort_dir=desc&count={COUNT}&appid=' + self.app_id + '&norender=1'),
                    self.parse_item)
        else:
            url = response.url
            parsed = urlparse.urlparse(url)
            start = int(parse_qs(parsed.query)['start'][0])
            yield Request(response.urljoin(
                f'?query=&start={start + COUNT}&search_descriptions=0&sort_column=price&sort_dir=desc&count={COUNT}&appid=' + self.app_id + '&norender=1'),
                self.parse_item)

    def close(spider, reason):
        csv_file = max(glob.iglob('*.csv'), key=os.path.getctime)

        wb = Workbook()
        ws = wb.active

        with open(csv_file, 'r', encoding="utf8") as f:
            for row in csv.reader(f):
                ws.append(row)

        wb.save(csv_file.replace('.csv', '') + '.xlsx')
