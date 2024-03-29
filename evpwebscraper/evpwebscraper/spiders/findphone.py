# -*- coding: utf-8 -*-
import scrapy
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

from .. conf import *
from .. helper_functions import *

def filter_text(text):
    pattern = re.compile("\(?[0-9]{3}\)?(\s|-|\.)*\(?[0-9]{3}\)?(\s|-|\.)*\(?[0-9]{4}\)?") # Regex for phone num
    results = re.search(pattern, text)
    return results

class FindphoneSpider(scrapy.Spider):
    name = 'findphone'

    def __init__(self, DATA_FILE_IN, search_for=SEARCH_FOR, **kwargs):
        self.towns = read_in_data(DATA_FILE_IN)
        self.start_urls = [list(town.values())[-1] for town in self.towns] # Last index is town website
        self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]
        # Print Headers
        self.headers = list(self.towns[0].keys())
        self.headers.append('{} Clerk Phone'.format(search_for[0].upper() + search_for[1:]))
        self.headers.append('Notes')
        FEED_EXPORT_FIELDS = self.headers
        print(','.join(self.headers))
        super().__init__(**kwargs)  # python

    def start_requests(self):
        # Attach and index to the requests
        for index, url in enumerate(self.start_urls):
            yield scrapy.Request(url, callback=self.parse, errback=self.parse_error, dont_filter=True, meta={'index': index})

    def parse(self, response):
        # Correspond information with town
        index = response.meta['index']
        values = list(self.towns[index].values())
        
        # Get html Using lxml parser 
        html = BeautifulSoup(response.text, 'lxml')
        
        # Remove javascript and stylesheets
        for script in html(["script", "style"]):
            script.decompose()
       
        # Remove elements that aren't displayed
        for element in html.select('[style="display:none"]'):
            element.decompose()
        for element in html.select('[style="visibility:hidden"]'):
            element.decompose()

        # Clean up remaining text and look for phone numbers
        # Phone numbers will be in string format number;number
        text = html.find_all(text=True, recursive=True)
        lines = []
        notes = ''
        for t in text:
            if 'fax' in t.lower() and 'fax' not in notes:
                notes = notes + "Some numbers are fax numbers "
            if 'assistant' in t.lower() and 'assistant' not in notes:
                notes = notes + "Some numbers are for assistant clerk or other administrative positions "
            line = filter_text(t)
            if not line is None and not line.string[line.start(0):line.end(0)] in lines:
                lines.append(line.string[line.start(0):line.end(0)])
        phone = ';'.join(lines)

        values.append(phone)
        if notes != '':
            notes = notes + " Try first number for town clerk phone"
        if phone == '':
            notes = "Phone number not found try checking website manually"
        values.append(notes)
        print(','.join(values))
        yield dict(zip(self.headers, values))

    def parse_error(self, failure):
        # Returns original values and note on failure
        # Correspond information with town
        index = failure.request.meta['index']
        error = failure.getErrorMessage()
        
        values = list(self.towns[index].values())
        values.append('') # Phone number string, empty here
        values.append(error)

        print(','.join(values))
        yield dict(zip(self.headers, values))

