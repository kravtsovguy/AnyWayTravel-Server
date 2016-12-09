# -*- coding: utf-8 -*-

from flask import Flask, request, Response
import urllib
import os

from myjson import jsonify
import trains
import avia

app = Flask(__name__)

@app.route("/")
def page_hello():
    return "Hello World!"

'''
    get IATA code of a city by it's name in russian
    example: http://127.0.0.1:5000/places_avia?name=Москва
'''
@app.route("/places_avia")
def page_places_avia():
    return jsonify(avia.find_places(request.args.get('name')))

'''
    get all tickets info between two points
    example - http://127.0.0.1:5000/tickets?origin=MOSC-sky&destination=OMS-sky&date=2016-12-29 
    'MOW','OMS','2016-12-29'
    date format - yyyy-MM-dd or yyyy-MM
    documentation - https://support.business.skyscanner.net/hc/en-us/articles/
'''
@app.route("/tickets")
def page_tickets():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if 'raw' in request.args:
        return jsonify(avia.get_tickets_rawdata(origin, destination, date))

    return jsonify(avia.get_tickets(origin, destination, date))

@app.route("/trains")
def page_trains():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if 'raw' in request.args:
        return jsonify(trains.get_tickets_rawdata(origin, destination, date))

    return jsonify(trains.get_tickets(origin, destination, date))

#######################

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)