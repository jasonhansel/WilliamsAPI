import urllib.request
import xml.etree.ElementTree as ET
import http.cookiejar
from bs4 import BeautifulSoup
import html.parser
import re
import json

non_decimal = re.compile(r'[^\d]+')

def handleItemPanel(str):
    root = BeautifulSoup(str, "html.parser")
    # also do td:only-child
    for row in root.select('tr'):
        if len(row.select('th')):
            continue
        if len(row.contents) >= 2:
            print('    ', ' '.join(row.contents[1].stripped_strings))
        else:
            print('    ', row.contents[0].string)

def handleMenuID(id):
    params = bytes(urllib.parse.urlencode({'menuOid': id}), 'utf-8')
    r2 = opener.open("http://nutrition.williams.edu/NetNutrition/1/Menu/SelectMenu", params)
    with r2 as response:
        page = response.read()
        data = {x['id'] : x['html'] for x in json.loads(page)['panels']}
        if data['itemPanel']:
            handleItemPanel(data['itemPanel'])

def handleChildID(id):
    params = bytes(urllib.parse.urlencode({'unitOid': id}), 'utf-8')
    r2 = opener.open("http://nutrition.williams.edu/NetNutrition/1/Unit/SelectUnitFromChildUnitsList", params)
    with r2 as response:
        page = response.read()
        data = {x['id'] : x['html'] for x in json.loads(page)['panels']}
        # FIXME: do the below
        if data['menuPanel']:
            root = BeautifulSoup(data['menuPanel'], 'html.parser')
            for table in root.select('.cbo_nn_menuCell > table'):
                print('TEST')
                name = table.contents[0].select_one('td').string
                print('    ', name)
                for menu in table.select('.cbo_nn_menuLink'):
                    id = non_decimal.sub('', menu.attrs['onclick'])
                    print('        ', menu.string)
                    handleMenuID(id)
        if data['itemPanel']:
            handleItemPanel(data['itemPanel'])


def handleID(id):
    params = bytes(urllib.parse.urlencode({'unitOid': id}), 'utf-8')
    r2 = opener.open("http://nutrition.williams.edu/NetNutrition/1/Unit/SelectUnitFromSideBar", params)
    with r2 as response:
        page = response.read()
        data = json.loads(page)['panels']
        inner = [x['html'] for x in data if x['id'] == 'childUnitsPanel'][0]
        root = BeautifulSoup(inner, "html.parser")
        for el in root.select('a'):
            print('  ', el.string)
            id = non_decimal.sub('', el.attrs['onclick'])
            # print('  ', id)
            handleChildID(id)

# https://stackoverflow.com/questions/554446/how-do-i-prevent-pythons-urllib2-from-following-a-redirect
class NoRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(r, f, c, m, h, u, x):
        return None
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
r = opener.open("http://nutrition.williams.edu/NetNutrition/")


with r as response:
    page = response.read()
    root = BeautifulSoup(page, "html.parser")
    for el in root.select('.cbo_nn_sideUnitPanelDiv .cbo_nn_sideUnitTable a'):
        print(el.string)
        id = non_decimal.sub('', el.attrs['onclick'])
        handleID(id)

    #     ) ET.fromstring(page, parser=ET.XMLParser(html=1))
    # links = root.findall(".//[@class='cbo_nn_sideUnitTable']//a")
    # for link in links:
    #     print(link.text)
