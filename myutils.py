import requests
import time
import json
from requests import Request

def poll_request(uri, cookies = None, params = {}, timeout = 20, sleep = 1, headers = {}, result_return_condition = (lambda r: True)):
    r = {}
    while timeout > 0:
        timeout-=1

        s = requests.session()
        if cookies:
            s.cookies = cookies
        req = Request('GET', uri, params=params, headers=headers)
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