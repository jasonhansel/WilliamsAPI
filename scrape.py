
# BUG: doesn't get Whitmans' data correctly
# Check through to make sure other data is correct

# Get all NetNutrtion data, and dump the result to stdout.

import urllib.request
import xml.etree.ElementTree as ET
import http.cookiejar
from bs4 import BeautifulSoup
from collections import namedtuple
import html.parser
import re
import json

non_decimal = re.compile(r'[^\d]+')

# class ComplexEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, complex):
#             return [obj.real, obj.imag]
#         # Let the base class default method raise the TypeError
#         return json.JSONEncoder.default(self, obj)
# print(json.dumps(2 + 1j, cls=ComplexEncoder))

# exit()

# see https://stackoverflow.com/questions/5906831/serializing-a-python-namedtuple-to-json
# class MyEncoder(json.JSONEncoder):
#     def iterencode(self, obj, **kwargs):
#         if(getattr(obj, '_asdict', None)):
#             obj = obj._asdict()
#         return json.JSONEncoder.iterencode(self, obj, **kwargs)

#     def encode(self, obj):
#         if(getattr(obj, '_asdict', None)):
#             obj = obj._asdict()
#         return json.JSONEncoder.encode(self, obj)

MealInfo = namedtuple('MealInfo', 'date meal menu')
MenuSection = namedtuple('MenuSection', 'name items')

def handleItemPanel(str):
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


def handleMenuID(id):
    params = bytes(urllib.parse.urlencode({'menuOid': id}), 'utf-8')
    r2 = opener.open("http://nutrition.williams.edu/NetNutrition/1/Menu/SelectMenu", params)
    with r2 as response:
        page = response.read()
        data = {x['id'] : x['html'] for x in json.loads(page)['panels']}
        return handleItemPanel(data['itemPanel'])

def handleResponse(page):
    data = {x['id'] : x['html'] for x in json.loads(page)['panels']}
    if data['childUnitsPanel']:
        root = BeautifulSoup(data['childUnitsPanel'], "html.parser")
        return { el.string : handleChildID(non_decimal.sub('', el.attrs['onclick']))
            for el in root.select('a')}
    if data['menuPanel']:
        root = BeautifulSoup(data['menuPanel'], 'html.parser')
        arr = []
        for table in root.select('.cbo_nn_menuCell > table'):
            name = table.contents[0].select_one('td').string
            date = name
            for menu in table.select('.cbo_nn_menuLink'):
                id = non_decimal.sub('', menu.attrs['onclick'])
                meal = menu.string
                arr.append(MealInfo(date, meal, handleMenuID(id)))
        return [a._asdict() for a in arr]
    if data['itemPanel']:
        return handleItemPanel(data['itemPanel'])

def handleChildID(id):
    params = bytes(urllib.parse.urlencode({'unitOid': id}), 'utf-8')
    r2 = opener.open("http://nutrition.williams.edu/NetNutrition/1/Unit/SelectUnitFromChildUnitsList", params)
    with r2 as response:
        page = response.read()
        return handleResponse(page)

def handleID(id):
    params = bytes(urllib.parse.urlencode({'unitOid': id}), 'utf-8')
    r2 = opener.open("http://nutrition.williams.edu/NetNutrition/1/Unit/SelectUnitFromSideBar", params)
    with r2 as response:
        page = response.read()
        return handleResponse(page)

# https://stackoverflow.com/questions/554446/how-do-i-prevent-pythons-urllib2-from-following-a-redirect
class NoRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(r, f, c, m, h, u, x):
        return None
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def getData():
    r = opener.open("http://nutrition.williams.edu/NetNutrition/")
    with r as response:
        page = response.read()
        root = BeautifulSoup(page, "html.parser")
        return { el.string : handleID(non_decimal.sub('', el.attrs['onclick']))
            for el in root.select('.cbo_nn_sideUnitPanelDiv .cbo_nn_sideUnitTable a')}

# enc = MyEncoder()

# print(enc.encode(getData()))
print(json.dumps(getData()))

    #     ) ET.fromstring(page, parser=ET.XMLParser(html=1))
    # links = root.findall(".//[@class='cbo_nn_sideUnitTable']//a")
    # for link in links:
    #     print(link.text)
