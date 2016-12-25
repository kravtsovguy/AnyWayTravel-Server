# -*- coding: utf-8 -*-

import myutils
import avia
import trains

from myjson import jsonify

import json
import codecs


def select_cities(cities):
    fav_cities = [ 
        'Москва',
        'Санкт-Петербург',
        'Калининград',
        'Челябинск',
        'Омск',
        'Новосибирск',
        'Тюмень',
        'Владивосток'
        ]

    new = []
    for c in cities:
        #if c['country_code'] == 'RU':
        if c['name'] in fav_cities:
            new.append(c)

    return new
    print('left %d cities with country_code "RU"' % len(cities))

    #cache_avia(new)

    #f = codecs.open('cities_ru.json', 'w', 'utf-8')
    #f.writelines(json.dumps(new, indent = 2, ensure_ascii = False))
    #f.close()

def cache_trains(cities):
    tot = pow(len(cities),2)

    f = codecs.open('trains_cache.json', 'w', 'utf-8', buffering = 0)
    f.write('[')

    for a in cities:
        for b in cities:
            if not a==b:
                tries = 10
                results = { }
                while not 'route' in results:
                    results = trains.get_tickets(a['name'], b['name'], '2017-01-25')
                    tries -= 1
                    if tries <= 0:
                        break
                tot -= 1

                if 'route' in results:
                    print('found %d paths from %s to %s' % (len(results['route']['paths']), a['name'], b['name']), '\t', tot)
                    f.write(json.dumps(results['route'], ensure_ascii = False)+',\n')
                else:
                    print('SKIPPED %s %s\n\t%s' % (a['name'], b['name'], str(results)))

    f.write(']')
    f.close()

def cache_avia(cities):
    tot = pow(len(cities),2)

    f = codecs.open('avia_cache.json', 'w', 'utf-8', buffering = 0)
    f.write('[')

    for a in cities:
        for b in cities:
            if not a==b:
                tries = 10
                results = { }
                while not 'route' in results:
                    results = avia.get_tickets(a['name'], b['name'], '2017-01-25')
                    tries -= 1
                    if tries <= 0:
                        break
                tot -= 1

                if 'route' in results:
                    print('found %d paths from %s to %s' % (len(results['route']['paths']), a['name'], b['name']), '\t', tot)
                    f.write(json.dumps(results['route'], ensure_ascii = False)+',\n')
                else:
                    print('SKIPPED %s %s\n\t%s' % (a['name'], b['name'], str(results)))

    f.write(']')
    f.close()

    