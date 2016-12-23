# -*- coding: utf-8 -*-

import requests
import time
import json
import re
import avia
import codecs

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

#LOAD CITIES BASE INTO MEMORY
def preload_cities_info():
    global cities_info
    global cities_info_raw

    f = codecs.open('cities.json', 'r', 'utf_8')
    cities_info = json.loads(f.read())
    f.close()

    #cities_info_raw = requests.get('https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru').json()['response']

    #cities_info_hash = { }
    #for x in cities_info_raw:
    #    if not x['name'] in cities_info_hash:
    #        cities_info_hash[x['name']] = []
    #    cities_info_hash[x['name']].append(x)

    #print(len(cities_info))
    #cities_full_info = []
    #for x in cities_info:
    #    #print(x['name'])
    #    inf = 0 if not x['name'] in cities_info_hash else cities_info_hash[x['name']]
    #    if not inf == 0 and len(inf) > 0:
    #        if len(inf) == 0:
    #            print('woot')
    #        x['country_code'] = inf[0]['country_code']
    #        x['code'] = inf[0]['code']
    #        cities_full_info.append(x)
    #        del inf[0]

    #f = codecs.open('cities2.json','w','utf-8')
    #f.writelines(json.dumps(cities_full_info, indent = 2, ensure_ascii = False))
    #f.close()

    print('loaded %d cities from cities.json' % len(cities_info))
preload_cities_info()

def find_cities(name_part, limit = 100):
    '''get array of city names by a part of it's names
    '''
    global cities_info

    regexp = re.compile(r'(^|\W)%s' % name_part, re.IGNORECASE)
    res = [x for x in cities_info if regexp.search(x['name']) is not None]
    #for r in res:
    #    aviaplaces = avia.find_places(r['name'])
    #    r['PlaceId'] = '' if len(aviaplaces) == 0 else aviaplaces[0]['PlaceId']
    res.sort(key = lambda k: k['name'])
    return ([x for x in res if x['country'] == 'Россия'] + [x for x in res if not x['country'] == 'Россия'])[:limit]

def get_city(city_name):
    '''get info of a city by it's name in russian
    '''
    global cities_info
    return next(x for x in cities_info if x['name'].lower() == city_name.lower())

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
    
    cities_found = find_cities(placename)
    places_found = avia.find_places(placename)
    res = { }

    if len(places_found) == 0:
        res = {
            'id' : '',
            'iata' : '' if len(cities_found) == 0 else cities_found[0]['code'],
            'name' : placename if len(cities_found) == 0 else cities_found[0]['name'],
            'country' : '' if len(cities_found) == 0 else cities_found[0]['country'],
            'city' : placename if len(cities_found) == 0 else cities_found[0]['name']
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