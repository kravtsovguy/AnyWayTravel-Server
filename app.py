# -*- coding: utf-8 -*-

from flask import Flask, request, Response
import urllib
import os

from myjson import jsonify
import trains
import avia
import myutils
from time import gmtime, strftime
import time

app = Flask(__name__)

import sys
# sys.setdefaultencoding() does not exist, here!
#reload(sys)  # Reload does the trick!
print(sys.getdefaultencoding())

requests_count = 0
requests_log = ''
start_time = time.time()

def inc_requests_counter():
    return 0
    global requests_count
    requests_count += 1
    global requests_log
    url = urllib.parse.unquote(request.full_path)
    requests_log += '<p>{t}    {ip}    <a href="{u}">{u}</a></p>\n'.format(u = url, t = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()), ip = request.remote_addr)

@app.route("/log")
def page_log():
    m, s = divmod(time.time() - start_time, 60)
    h, m = divmod(m, 60)
    uptime = '<p>Uptime: %d:%02d:%02d</p>\n' % (h, m, s)
    return uptime + requests_log

@app.route("/test")
def page_test():
    from os import listdir, getcwd
    from os.path import isfile, join
    a = listdir(getcwd())

    s = '<p>Valid links:</p>\n'
    arr = [
        "/city_suggestions?namepart=пете&limit=5",
         "/tickets?origin=москва&destination=омск&date=2016-12-29",
         "/trains?origin=москва&destination=омск&date=2016-12-29"
         ]
    for l in arr: s += '<p><a href="{url}">{url}</a></p>\n'.format(url = l)
    s += '<p>Invalid links:</p>\n'
    arr = [
        "/places_avia?name=Лосино-Петровский",
        "/tickets?origin=хххххх&destination=омск&date=2016-12-29",
        "/trains?origin=хххххх&destination=adasdasd&date=2016-10-29",
        "/trains?origin=омск&destination=Лосино-Петровский&date=2016-10-29"
        ]
    for l in arr: s += '<p><a href="{url}">{url}</a></p>\n'.format(url = l)

    s += '<p>Requests completed: %d</p>' % requests_count

    return s +'\n\n'+ str(a)

@app.route("/")
def page_hello():
    return "Hello World!"

@app.route("/places_avia")
def page_places_avia():
    inc_requests_counter()
    return jsonify(avia.find_places(request.args.get('name')))

@app.route("/tickets")
def page_tickets():
    """Get all tickets info between two points.
    """
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if 'raw' in request.args:
        inc_requests_counter()
        return jsonify(avia.get_tickets_rawdata(origin, destination, date))

    inc_requests_counter()
    return jsonify(avia.get_tickets(origin, destination, date))

@app.route("/trains")
def page_trains():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    date = request.args.get('date')

    if 'raw' in request.args:
        inc_requests_counter()
        return jsonify(trains.get_tickets_rawdata(origin, destination, date))

    inc_requests_counter()
    return jsonify(trains.get_tickets(origin, destination, date))

@app.route("/city_suggestions")
def page_city_suggestions():
    try:
        namepart = request.args.get('namepart')
        limit = 100 if not 'limit' in request.args else int(request.args.get('limit'))
        inc_requests_counter()
        return jsonify(myutils.find_cities(namepart, limit))
    except:
        return("Unexpected error:", sys.exc_info()[0])

#######################

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

