# -*- coding: utf-8 -*-

"""

 OneTwoTrip API

 everywhere IATA codes

"""

import requests
import json
import time

import myutils

apikey = 'affiliate-test'

def get_tickets(origin, destination, date, only_direct=False):
    '''
    :param origin: OMS
    :param destination: VVO
    :param date: 2016-12-29
    '''
    return format_tickets_data(get_tickets_rawdata(origin, destination, date), only_direct)

def get_tickets_rawdata(origin, destination, date):
    parseddate = date.split('-')[2] + date.split('-')[1]

    params = {
        'ad' : 1,
        'cn' : 0,
        'in' : 0,
        'cs' : 'E',
        'route' : parseddate + origin + destination,
        'currency' : 'RUB',
        'ott4862' : 'true',
        '_' : '1485378645500'
        #'source' : apikey
        }
    
    r = requests.post('https://www.onetwotrip.com/_api/searching/startSync2/', data = params)

    result = r.json()
    result['route'] = params['route']
    result['from'] = origin
    result['to'] = destination
    result['date'] = date
    return result

def format_tickets_data(data, only_direct=False):
    if not 'frs' in data:
        return data

    paths = []

    for fr in data['frs']:
        #try:
            if only_direct and len(fr['dirs'][0]['trps']) > 1:
                continue
            
            segments = []

            for trp in fr['dirs'][0]['trps']:
                trpInf = data['trps'][trp['id']]
                trpInf['cls'] = trp['cls']
                trpInf['srvCls'] = trp['srvCls']
                trpInf['stAvl'] = trp['stAvl']
                trpInf['eTkAvail'] = trp['eTkAvail']
                #trpInf['​avlSrc'] = trp['avlSrc']
                trpInf['​fic'] = trp['fic']

                duration = int(trpInf['fltTm'][:2])*60 + int(trpInf['fltTm'][-2:])

                segments.append({
                    'type' : 'Plane',
                    'origin' : myutils.make_place_by_iata(trpInf['from']),
                    'destination' : myutils.make_place_by_iata(trpInf['to']),
                    'departure' : date_time(trpInf['stDt'], trpInf['stTm']),
                    'arrival' : date_time(trpInf['endDate'], trpInf['endTm']),
                    'duration' : duration,
                    'pricing' : [],
                    'carrier' : {
                        'name' : trpInf['airCmp'],
                        'image' : 'https://www.onetwotrip.com/images/ak/small/'+trpInf['airCmp']+'.png',
                        'imageAlt' : 'http://s1.apideeplink.com/images/airlines/'+trpInf['airCmp']+'.png',
                        'flightNumber' : trpInf['fltNm'],
                        'code' : trpInf['airCmp']
                        }
                    })

            if len(segments) > 0:
                segments[0]['pricing'] = [{
                    'price' : fr['pmtVrnts']['transactions'][0]['total'],
                    'currency' : fr['pmtVrnts']['transactions'][0]['cur'],
                    'link' : "",
                    'agent' : {
                        'name' : 'OneTwoTrip',
                        'image' : 'https://www.onetwotrip.com/images/OTTLogo.svg'
                        }
                    }]

                segments[0]['bookingInfo'] = {
                    'gdsInfo' : data['gdsInfs'][fr['gdsInf']]['hash'],
                    'fareKey' : fr['frKey'],
                    'customerLanguage' : 'ru',
                    'routeKey' : data['route'],
                    
                    'trips' : []
                    }


            paths.append({
                'segments':segments
                })
        #except:
            #print('error : there are some invalid data from skyscanner api')

    return {
        'route': {
            'origin' : data['from'],
            'destination' : data['to'],
            'departure' : data['date'],
            'paths' : paths
            }
        }

def date_time(date, time):
    ''' takes 20170301 and 2140
    returns 2017-12-30T04:15:00
    '''

    return date[:4] + '-'+ date[4:-2] + '-' + date[-2:] + 'T' + time[:2] + ':' + time[-2:] + ':00'