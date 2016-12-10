# -*- coding: utf-8 -*-

import requests
import time
import json
import re
import avia

def poll_request(uri, cookies = None, params = {}, timeout = 20, sleep = 1, headers = {}, result_return_condition = (lambda r: True)):
    r = {}
    while timeout > 0:
        timeout-=1

        s = requests.session()
        if cookies:
            s.cookies = cookies
        req = requests.Request('GET', uri, params=params, headers=headers)
        prepped = req.prepare()
        req = s.send(prepped)


        print("code: " + str(req.status_code))
        if req.status_code == 200:
            r = req.json()

            print(req.request.url)
            if 'result' in r:
                if r['result'].lower() == 'error':
                    return r

            if result_return_condition(r):
                return r

        time.sleep(1)
    return {'error':'timed out'}

import citites_container
cities_names = citites_container.cities
def find_cities(name_part, limit = 100):
    '''get array of city names by a part of it's names
    '''
    global cities_names

    regexp = re.compile(r'(^|\W)%s' % name_part, re.IGNORECASE)
    res = [x for x in cities_names if regexp.search(x['name']) is not None][:limit]
    #for r in res:
    #    aviaplaces = avia.find_places(r['name'])
    #    r['PlaceId'] = '' if len(aviaplaces) == 0 else aviaplaces[0]['PlaceId']
    return res

cities_info = requests.get('https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru').json()['response']
def get_iata(city_name):
    '''get IATA code of a city by it's name in russian
    '''
    global cities_info
    city_name = city_name.lower()
    return str(next(x for x in cities_info if x['name'].lower() == city_name))

'''
city.json and country.json was generated from csv files https://habrahabr.ru/post/21949/
cities = json.loads(open('city.json', 'r').read())
countries = json.loads(open('country.json', 'r').read())
cities = [{'name':x['name'], 'country': next(y['name'] for y in countries if y['country_id'] == x['country_id'])} for x in cities]
c = open('c.json', 'w')
c.write(json.dumps(cities, ensure_ascii=False, indent = 2))
c.close()
'''

places_cache = { }
def find_make_place(placename):
    global places_cache
    if placename in places_cache:
        return places_cache[placename]

    places_found = avia.find_places(placename)
    res = { }

    if len(places_found) == 0:
        cities_found = find_cities(placename)
        res = {
            'id' : '',
            'iata' : '',
            'name' : placename if len(cities_found) == 0 else cities_found[0]['name'],
            'country' : '' if len(cities_found) == 0 else cities_found[0]['country'],
            'city' : p['PlaceName'].split(" ")[0]
        }
    else:
        p = places_found[0]    
        res = {
            'id' : p['PlaceId'],
            'iata' : p['PlaceId'].split("-")[0],
            'name' : p['PlaceName'],
            'country' : p['CountryName'],
            'city' : p['PlaceName'].split(" ")[0]
        }

    places_cache[placename] = res
    return res

def check_zero_len(o, d, o_description, d_description, error_text = 'error-text'):
    if len(o) == 0 or len(d) == 0:
        details = []
        if len(o) == 0: details.append(o_description)
        if len(d) == 0: details.append(d_description)
        return {
            'error':error_text, 
            'details':str(details)
            }
    return 'ok'