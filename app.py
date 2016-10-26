import os
import requests
import json
from flask import Flask, request
app = Flask(__name__)
cities_info = None
headers = {"X-Access-Token": "8bfc8f2a2c28ae32b9c76fca9c50c360"}

@app.route("/")
def hello():
    return "Hello World!"

#example http://127.0.0.1/city_code?name=Москва
@app.route("/city_code")
def avia():
    return get_iata(request.args.get('name'))

#
@app.route("/tickets")
def tickets():
    origin = request.args.get('origin')
    destination = request.args.get('destination')

    return str(get_avia_info_latestPrices(origin, destination))


def get_avia_info_latestPrices(origin, destination, period_type = 'year', one_way = 'true', page = 1, limit = 30, show_to_affiliates = 'false', trip_class = 0, trip_duration = 100):
    endpoint = "http://api.travelpayouts.com/v2/prices/latest"
    params = {
            'currency':'rub',
            'sorting':'price',
            'origin':origin,
            'destination':destination,
            'period_type':period_type,
            'one_way':one_way,
            'page':str(page),
            'limit':str(limit),
            'show_to_affiliates':show_to_affiliates,
            'trip_class':trip_class
        }
    response = requests.get(endpoint, params = params, headers = headers)
    return response.json()

def get_avia_tickets(origin, destination, depart_date, return_date):
    
    return ""

def get_iata(city_name):
    
    endpoint = 'https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru'

    global cities_info
    if cities_info is None:
        cities_info = requests.get(endpoint).json()['response']
        
    return str(next(x for x in cities_info if x['name'] == city_name))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)