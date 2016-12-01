# -*- coding: utf-8 -*-

import os
import requests
import json
from flask import Flask, request
import urllib
import time
from flask.json import jsonify

app = Flask(__name__)

cities_info = None

#travelpayouts.com token
travelpayoutsheaders = {"X-Access-Token": "8bfc8f2a2c28ae32b9c76fca9c50c360"}
#skyscanner token
skyscannerapikey = 'prtl6749387986743898559646983194'#'ba429833397294416692521632122922'

########### pages ###########

@app.route("/")
def page_hello():
    return "Hello World!"

#get IATA code of a city by it's name in russian
#example http://127.0.0.1:5000/places_avia?name=Москва
@app.route("/places_avia")
def page_places_avia():
    return jsonify(autosuggest_list(request.args.get('name')))

#get all tickets info between two points
#example
#http://127.0.0.1:5000/tickets?origin=MOW&destination=OMS&date=2016-12-29
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
        return str(get_tickets_data(origin, destination, date))

    return jsonify(get_formated_tickets_data(get_tickets_data(origin, destination, date)))

########### ##### ###########

def autosuggest_list(name):
    return requests.get('http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/RU/RUB/ru-RU?query=' + name + '&apiKey=' + skyscannerapikey, headers = {'Accept' : 'application/json'}).json()

#get IATA code of city by it's name in russian
def get_iata(city_name):
    global cities_info
    if cities_info is None:
        cities_info = requests.get('https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru').json()['response']
        
    return str(next(x for x in cities_info if x['name'] == city_name))

#json data (not string) of tickets between two points
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

    air_formatted = []

    for leg in data['Legs']:
        
        origin_place = next(x for x in data['Places'] if x['Id'] == leg['OriginStation'])
        destination_place = next(x for x in data['Places'] if x['Id'] == leg['DestinationStation'])
        #carriers = [x for x in data['Carriers'] if x['Id'] in leg['Carriers']]
        segments = [format_segment(x, data) for x in data['Segments'] if x['Id'] in leg['SegmentIds']]
        pricing_options = next(x for x in data['Itineraries'] if x['OutboundLegId'] == leg['Id'])['PricingOptions']

        for option in pricing_options:
            option['Agent'] = next(x for x in data['Agents'] if x['Id'] == option['Agents'][0])
            option.pop('Agents')
            option.pop('Status')

        air_formatted.append({
            'type':'flight',
            'origin':format_place(origin_place, data['Places']),
            'destination':format_place(destination_place, data['Places']),
            'lowestprice':pricing_options[0]['Price'],
            'pricing':pricing_options,
            'departure':leg['Departure'],
            'arrival':leg['Arrival'],
            #'carriers':carriers,
            'segments':segments
            })

    return {
        #place ids in 'Query' are strings but anywhere else they are integers
        'origin':format_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['OriginPlace'])),data['Places']),
        'destination':format_place(next(x for x in data['Places'] if x['Id'] == int(data['Query']['DestinationPlace'])),data['Places']),
        'departure':data['Query']['OutboundDate'],
        'routes':air_formatted
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)