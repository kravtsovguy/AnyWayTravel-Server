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

def get_tickets(origin, destination, date):
    '''
    :param origin: Москва
    :param destination: Омск
    :param date: 2016-12-29
    '''
    return format_tickets_data(get_tickets_rawdata(origin, destination, date))

def get_tickets_rawdata(origin, destination, date):

    o = find_places(origin)
    d = find_places(destination)

    check = myutils.check_zero_len(o, d, origin, destination, 'no such airport')
    if not check == 'ok':
        return check
    
    #print('searchin [orig "%s" found "%s"]' % (origin, o[0]))
    #print('searchin [dest "%s" found "%s"]' % (destination, d[0]))

    o = o[0]['PlaceId']
    d = d[0]['PlaceId']

    params = {
        'apiKey':apikey,
        'outbounddate':date,
        'country':'RU',
        'currency':'RUB',
        'locale':'ru-RU',
        'originplace':o,
        'destinationplace':d
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
        try:
            segments = []

            for segid in leg['SegmentIds']:
                    seg = next(x for x in data['Segments'] if x['Id'] == segid)
                    carry = next(x for x in data['Carriers'] if x['Id'] == seg['Carrier'])

                    segments.append({
                        'type' : 'Plane',
                        'origin' : myutils.find_make_place(next(x for x in data['Places'] if x['Id'] == seg['OriginStation'])['Name']),
                        'destination' : myutils.find_make_place(next(x for x in data['Places'] if x['Id'] == seg['DestinationStation'])['Name']),
                        'departure' : seg['DepartureDateTime'], 
                        'arrival' : seg['ArrivalDateTime'],  
                        'duration' : int(seg['Duration']),
                        'pricing' : [],
                        'carrier' : {
                            'name' : carry['Name'],
                            'image' : carry['ImageUrl'],
                            'flightNumber' : seg['FlightNumber'],
                            'code' : carry['Code']
                            }
                        })

            if len(segments) > 0:
                segments[0]['pricing'] = make_pricing_options(next(x for x in data['Itineraries'] if x['OutboundLegId'] == leg['Id'])['PricingOptions'], data)

            paths.append({
                'segments':segments
                })
        except:
            print('error : there are some invalid data from skyscanner api')

    return {
        'route': {
            'origin' : myutils.find_make_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['OriginPlace']))['Name']),
            'destination' : myutils.find_make_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['DestinationPlace']))['Name']),
            'departure' : data['Query']['OutboundDate'],
            'paths' : paths
            }
        }

def make_pricing_options(options, data):
    res = []
    for opt in options:
        agent = next(x for x in data['Agents'] if x['Id'] == opt['Agents'][0])
        res.append({
            'price' : float(opt['Price']),
            'currency' : data['Query']['Currency'],
            'link' : opt['DeeplinkUrl'],
            'agent' : {
                'name' : agent['Name'],
                'image' : agent['ImageUrl']
            }
        })

    return res