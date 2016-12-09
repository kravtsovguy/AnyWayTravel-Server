# -*- coding: utf-8 -*-

"""

 SkyScanner API

 'prtl6749387986743898559646983194' public key
 'ba429833397294416692521632122922' our own key

"""

import requests
import json
import time

import myutils

apikey = 'prtl6749387986743898559646983194'

cities_info = None
places_cache = { }

'''
    returns an array of 
    { 
        'CountryId':'RU-sky',
        'RegionId':'',
        'CityId':'MOSC-sky',
        'CountryName':'Россия',
        'PlaceId':'MOSC-sky',
        'PlaceName':'Москва' 
    }
'''
def find_places(name=None, id=None):
    if (name and id) or (not name and not id):
        raise ValueError("Pass either name or id")

    p = { 'apiKey' : apikey }
    if name:
        p['query'] = name
    else:
        p['id'] = id

    return requests.get('http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/RU/RUB/ru-RU', params = p, headers = {'Accept' : 'application/json'}).json()['Places']

'''
    origin - MOSC-sky
    destination - OMS-sky
'''
def get_tickets(origin, destination, date):
    return format_tickets_data(get_tickets_rawdata(origin, destination, date))

def get_tickets_rawdata(origin, destination, date):
    params = {
        'apiKey':apikey,
        'outbounddate':'2016-12-29',
        'country':'RU',
        'currency':'RUB',
        'locale':'ru-RU',
        'originplace':(origin),
        'destinationplace':(destination)
        }
    r = requests.post('http://partners.api.skyscanner.net/apiservices/pricing/v1.0', data = params)

    if not ('Location' in r.headers):
        return r.json()

    fetchuri = r.headers['Location'] + '?apiKey=' + apikey

    return myutils.poll_request(fetchuri, 
                                headers = {"Accept":"application/json"}, 
                                result_return_condition = (lambda r: r['Status'] == 'UpdatesComplete'))

def format_tickets_data(data):
    if not 'Legs' in data:
        return data

    paths = []

    for leg in data['Legs']:
        segments = []

        for segid in leg['SegmentIds']:
            seg = next(x for x in data['Segments'] if x['Id'] == segid)
            carry = next(x for x in data['Carriers'] if x['Id'] == seg['Carrier'])

            segments.append({
                'type' : 'Plane',
                'origin' : find_make_place(next(x for x in data['Places'] if x['Id'] == seg['OriginStation'])['Name']),
                'destination' : find_make_place(next(x for x in data['Places'] if x['Id'] == seg['DestinationStation'])['Name']),
                'departure' : seg['DepartureDateTime'], 
                'arrival' : seg['ArrivalDateTime'],  
                'duration' : seg['Duration'],
                'pricing' : [],
                'carrier' : {
                    'name' : carry['Name'],
                    'image' : carry['ImageUrl'],
                    'flightNumber' : seg['FlightNumber'],
                    'code' : carry['Code']
                    }
                })

        segments[0]['pricing'] = make_pricing_options(next(x for x in data['Itineraries'] if x['OutboundLegId'] == leg['Id'])['PricingOptions'], data)

        paths.append({
            'segments':segments
            })

    return {
        'route': {
            'origin' : find_make_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['OriginPlace']))['Name']),
            'destination' : find_make_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['DestinationPlace']))['Name']),
            'departure' : data['Query']['OutboundDate'],
            'paths' : paths
            }
        }

def find_make_place(placename):
    global places_cache
    if placename in places_cache:
        return places_cache[placename]

    p = find_places(placename)[0]
    '''
    p
    {
        'CountryId' : 'RU-sky',
        'RegionId' : '',
        'CityId' : 'MOSC-sky',
        'CountryName' : 'Россия',
        'PlaceId' : 'MOSC-sky',
        'PlaceName' : 'Москва'
    }
    '''

    code = p['PlaceId'].split('-')[0]

    res = {
        'id' : p['PlaceId'],
        'iata' : p['PlaceId'].split("-")[0],
        'name' : p['PlaceName'],
        'country' : p['CountryName'],
        'city' : p['PlaceName'].split(" ")[0]
    }

    places_cache[placename] = res
    return res

def make_pricing_options(options, data):
    res = []
    for opt in options:
        agent = next(x for x in data['Agents'] if x['Id'] == opt['Agents'][0])
        res.append({
            'price' : opt['Price'],
            'currency' : data['Query']['Currency'],
            'link' : opt['DeeplinkUrl'],
            'agent' : {
                'name' : agent['Name'],
                'image' : agent['ImageUrl']
            }
        })

    return res

'''
    get IATA code of city by it's name in russian
'''
def get_iata(city_name):
    global cities_info
    if cities_info is None:
        cities_info = requests.get('https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru').json()['response']
    return str(next(x for x in cities_info if x['name'].lower() == city_name.lower()))