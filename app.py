# -*- coding: utf-8 -*-

import os
import requests
import json
from flask import Flask, request, Response
import urllib
import time

app = Flask(__name__)

cities_info = None
places_cache = { }

#travelpayouts.com token
travelpayoutsheaders = {"X-Access-Token": "8bfc8f2a2c28ae32b9c76fca9c50c360"}
#skyscanner token
skyscannerapikey = 'prtl6749387986743898559646983194' #public key
#skyscannerapikey = 'ba429833397294416692521632122922' #our key

def myjsonify(data):
    indent = None
    separators = (',', ':')

    if not request.is_xhr:
        indent = 2
        separators = (', ', ': ')

    return Response(
        (json.dumps(data, indent=indent, separators=separators, ensure_ascii=False), '\n'),
        mimetype='application/json'
    )











########### pages ###########

@app.route("/")
def page_hello():
    return "Hello World!"

#get IATA code of a city by it's name in russian
#example http://127.0.0.1:5000/places_avia?name=Москва
@app.route("/places_avia")
def page_places_avia():
    data = autosuggest_list(request.args.get('name'))
    
    return myjsonify(data)

#get all tickets info between two points
#example
#http://127.0.0.1:5000/tickets?origin=MOSC-sky&destination=OMS-sky&date=2016-12-29
#example - 'MOW','OMS','2016-12-29'
#valid date - yyyy-MM-dd or yyyy-MM
#documentation -
#https://support.business.skyscanner.net/hc/en-us/articles/211487049-Cheapest-quotes
@app.route("/tickets")
def page_tickets():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if 'raw' in request.args:
        return myjsonify((get_tickets_data(origin, destination, date)))

    return myjsonify(get_formated_tickets_data(get_tickets_data(origin, destination, date)))

########### ##### ###########













def autosuggest_list(name):
    return requests.get('http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/RU/RUB/ru-RU?query=' + name + '&apiKey=' + skyscannerapikey, headers = {'Accept' : 'application/json'}).json()

def get_place_info(placeid):
    return requests.get('http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/RU/RUB/ru-RU?id=' + placeid + '&apiKey=' + skyscannerapikey, headers = {'Accept' : 'application/json'}).json()

#get IATA code of city by it's name in russian
def get_iata(city_name):
    global cities_info
    if cities_info is None:
        cities_info = requests.get('https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru').json()['response']
        
    return str(next(x for x in cities_info if x['name'] == city_name))

#json data of tickets between two points
def get_tickets_data(origin, destination, date):
    params = {
        'apiKey':skyscannerapikey,
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

    fetchuri = r.headers['Location'] + '?apiKey=' + skyscannerapikey

    timeout = 20
    result = {}
    while timeout > 0:
        req = requests.get(fetchuri, headers = {"Accept":"application/json"})
        print("code: " + str(req.status_code))
        if req.status_code == 200:
            result = req.json()

            if result['Status'] == 'UpdatesComplete':
                return result

        time.sleep(1)

    return {'error':'timed out'}

def get_formated_tickets_data(data):
    if not 'Legs' in data:
        return data

    paths = []

    for leg in data['Legs']:
        segments = []

        for segid in leg['SegmentIds']:
            seg = next(x for x in data['Segments'] if x['Id'] == segid)
            carry = next(x for x in data['Carriers'] if x['Id'] == seg['Carrier'])

            segments.append({
                'origin' : make_place(next(x for x in data['Places'] if x['Id'] == seg['OriginStation'])),
                'destination' : make_place(next(x for x in data['Places'] if x['Id'] == seg['DestinationStation'])),
                'departure' : seg['DepartureDateTime'], 
                'arrival' : seg['ArrivalDateTime'],  
                'type' : 'Plane', # , Train
                'carrier' : {
                    'name' : carry['Name'],
                    'image' : carry['ImageUrl'],
                    'flightNumber' : seg['FlightNumber'],
                    'code' : carry['Code']
                    }
                })

        paths.append({
            'segments':segments,
            'pricing' : make_pricing_options(next(x for x in data['Itineraries'] if x['OutboundLegId'] == leg['Id'])['PricingOptions'], data)
            })

    return {
        'route': {
            'origin' : make_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['OriginPlace']))),
            'destination' : make_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['DestinationPlace']))),
            'departure' : data['Query']['OutboundDate'],
            'paths' : paths
            }
        }

def format_place(place, all):
    if 'ParentId' in place:
        place['Parent'] = next(x for x in all if x['Id'] == place['ParentId'])
        place.pop('ParentId')
        format_place(place['Parent'], all)

    return place

def format_segment(segment, data):
    origin_place = next(x for x in data['Places'] if x['Id'] == segment['OriginStation'])
    destination_place = next(x for x in data['Places'] if x['Id'] == segment['DestinationStation'])
    carrier = next(x for x in data['Carriers'] if x['Id'] == segment['Carrier'])

    segment = {
        'origin':format_place(origin_place, data['Places']),
        'destination':format_place(destination_place, data['Places']),
        'flightnumber':segment['FlightNumber'],
        'departure':segment['DepartureDateTime'],
        'arrival':segment['ArrivalDateTime'],
        'carrier':carrier
        }

    return segment

def make_place(placeinf):
    global places_cache

    if placeinf['Code'] in places_cache:
        return places_cache[placeinf['Code']]

    raw = get_place_info(placeinf['Code'])
    inf = {}
    if('Places' in raw):
        inf = raw['Places'][0]
    else:
        inf = autosuggest_list(placeinf['Name'])['Places'][0]

    res = {
        'id' : inf['PlaceId'],
        'iata' : inf['PlaceId'].split("-")[0],
        'name' : inf['PlaceName'],
        'country' : inf['CountryName'],
        'city' : inf['PlaceName'].split(" ")[0]
    }

    places_cache[placeinf['Code']] = res

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)