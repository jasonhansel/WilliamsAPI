#!/usr/bin/python

# Get NetNutrition data and dump to stdout.
# Run with 'test' to run a test (may fail if NetNutrition has been updated)

# TODO:
# - Support putting the output somewhere nice (eg. on S3)
# - AWS Lambda integration
# - Error handling


import urllib.request
import xml.etree.ElementTree as ET
import http.cookiejar
from bs4 import BeautifulSoup
from collections import namedtuple
import html.parser
import re
import sys
import json
import functools
import unittest

non_decimal = re.compile(r'[^\d]+')
MealInfo = namedtuple('MealInfo', 'date meal menu')
MenuSection = namedtuple('MenuSection', 'name items')

def handleItemPanel(opener,str):
    root = BeautifulSoup(str, "html.parser")
    # also do td:only-child
    sections = []
    for row in root.select('.cbo_nn_itemGridTable tr'):
        tds = row.select('td')
        if len(tds) >= 2:
            item = ' '.join(tds[1].stripped_strings)
            sections[-1].items.append(item)
        elif len(tds) > 0:
            header = tds[0].string
            sections.append(MenuSection(header, []))
    return [s._asdict() for s in sections]

def handleMenuPanel(opener,str):
    root = BeautifulSoup(str, 'html.parser')
    arr = []
    for table in root.select('.cbo_nn_menuCell > table'):
        date = table.contents[0].select_one('td').string
        for menu in table.select('.cbo_nn_menuLink'):
            ID = non_decimal.sub('', menu.attrs['onclick'])
            meal = menu.string
            yield MealInfo(date, meal, requestFromNN(opener, 'Menu/SelectMenu', 'menuOid', ID))

def handleResponse(opener, page):
    try:
        j = json.loads(page)
    except json.decoder.JSONDecodeError:
        return None
    data = {x['id'] : x['html'] for x in j['panels']}
    if data['childUnitsPanel']:
        root = BeautifulSoup(data['childUnitsPanel'], "html.parser")
        return { el.string : requestFromNN(opener,'Unit/SelectUnitFromChildUnitsList', 'unitOid', non_decimal.sub('', el.attrs['onclick']))
            for el in root.select('a')}
    if data['menuPanel']:
        return [a._asdict() for a in handleMenuPanel(opener, data['menuPanel'])]
    if data['itemPanel']:
        return handleItemPanel(opener, data['itemPanel'])

@functools.lru_cache()
def requestFromNN(opener, endpoint, param, ID):
    print('Request:', endpoint, param, ID)
    params = bytes(urllib.parse.urlencode({param: ID}), 'utf-8')
    r = opener.open(f"http://nutrition.williams.edu/NetNutrition/1/{endpoint}", params)
    with r as response:
        page = response.read()
        return handleResponse(opener, page)

def requestAllNN():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    r = opener.open("http://nutrition.williams.edu/NetNutrition/")
    with r as response:
        page = response.read()
        root = BeautifulSoup(page, "html.parser")
        return { el.string : requestFromNN(opener, 'Unit/SelectUnitFromSideBar', 'unitOid',  non_decimal.sub('', el.attrs['onclick']))
            for el in root.select('.cbo_nn_sideUnitPanelDiv .cbo_nn_sideUnitTable a')}

class SimpleTest(unittest.TestCase):
    # This test is only valid on 2017/08/15; NetNutrition may change
    # after that...
    def test_20170815(_):
        with open('output_20170815.json') as file:
            test = json.load(file)
            data = requestAllNN()
            out = open('output.json', 'w+')
            out.write(json.dumps(requestAllNN()))
            out.close()
            print(json.dumps(requestAllNN()))
            assert(test == data)


if len(sys.argv) > 1 and sys.argv[1] == 'test':
    unittest.main(argv=[ sys.argv[0] ])
else:
    print(json.dumps(requestAllNN()))
