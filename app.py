import os
import requests
import json
from flask import Flask, request
import urllib
app = Flask(__name__)
cities_info = None

#travelpayouts.com token
travelpayoutsheaders = {"X-Access-Token": "8bfc8f2a2c28ae32b9c76fca9c50c360"}
#skyscanner token
skyscannerapikey = 'ba429833397294416692521632122922'

@app.route("/")
def hello():
    return "Hello World!"

#example http://127.0.0.1:5000/city_code?name=Москва
@app.route("/city_code")
def avia():
    return get_iata(request.args.get('name'))

#example http://127.0.0.1:5000/tickets?origin=MOW&destination=OMS&date=2016-12-29
@app.route("/tickets")
def tickets():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    return str(get_tickets(origin, destination, date))

#documentation - https://support.business.skyscanner.net/hc/en-us/articles/211487049-Cheapest-quotes
#example -       get_tickets('MOW','OMS','2016-12-29')
#valid date -    yyyy-MM-dd or yyyy-MM
def get_tickets(origin, destination, date):
    endpoint = 'http://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/RU/RUB/ru-RU/'+origin+'/'+destination+'/'+date+'?apiKey='+skyscannerapikey

    return requests.get(endpoint, headers = {"Accept":"application/json"}).json()

#get IATA code of city by it's name in russian
def get_iata(city_name):
    global cities_info
    if cities_info is None:
        cities_info = requests.get('https://iatacodes.org/api/v6/cities?api_key=bb949559-7f63-460a-b5ad-affe75651a35&lang=ru').json()['response']
        
    return str(next(x for x in cities_info if x['name'] == city_name))







if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)