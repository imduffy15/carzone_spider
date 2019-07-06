# -*- coding: utf-8 -*-
import scrapy

import re
import json
from furl import furl


class PrimarySpider(scrapy.Spider):
    name = 'primary'
    allowed_domains = ['www.carzone.ie']
    start_urls = ['https://www.carzone.ie/search/result/cars/page/1/limit/30']

    def parse(self, response):
        yield scrapy.Request(response.url, callback=self.parse_search_listing)

    def parse_search_listing(self, response):
        js = response.selector.xpath('//script[@id="data"]/text()').extract()
        search_listing = json.loads(
            re.search("window.jsonData=(.*);", js[0])[1])

        adverts = search_listing['results']
        for advert in adverts:
            yield scrapy.Request(advert['url'], callback=self.parse_advert)

        pagination = search_listing['state']
        if pagination['totalPageNumber'] > pagination['page']:
            next_page = pagination['page'] + 1
            yield scrapy.Request(
                "https://www.carzone.ie/search/result/cars/page/{}/limit/30".
                format(next_page),
                callback=self.parse_search_listing)

    def parse_advert(self, response):
        js = response.selector.xpath('//script[@id="data"]/text()').extract()
        advert = json.loads(re.search("window.jsonData=(.*)",
                                      js[0])[1])['result']
        result = {
            'images': set(),
            'body_type': advert['bodyType'].lower(),
            'make': advert['make'].lower(),
            'model': advert['model'].lower(),
            'year': advert['year'].lower()
        }
        [
            result['images'].add(self.clean_image_url(url))
            for url in advert.pop('mainImageUrls', [])
        ]
        [
            result['images'].add(self.clean_image_url(url))
            for url in advert.pop('thumbnailImageUrls', [])
        ]
        [
            result['images'].add(self.clean_image_url(url))
            for url in advert.pop('largeImageUrls', [])
        ]
        yield result

    def clean_image_url(self, url):
        return furl(url).remove(
            args=['height', 'width', 'defaultImageUrl']).url
