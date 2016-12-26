

import search
import myutils
import avia
import trains

def get_tickets(origin, destination, date):
    origin = myutils.find_cities(origin)[0]['name']
    destination = myutils.find_cities(destination)[0]['name']
    print('get tickets ',origin,' ',destination)

    paths = []
    try:
        path_variants = search.get_paths(origin, destination)

        print('vars: ',len(path_variants))
    
        i = 0
        while i < len(path_variants):
        #for p in path_variants:
            p = path_variants[i]
            i += 1
       
            for a in p:
                ''' a - segment:     [ "Тюмень", "Москва" ], "plane"
                '''
                #try:
                if True:
                    print('get tickets',a[1],a[0][0],a[0][1])
                    if a[1] == 'plane':
                        raw = avia.get_tickets(a[0][0],a[0][1],date,True)
                        if not 'route' in raw:
                            print(str(raw))
                            return raw
                        a.append(raw['route'])
                    else:
                        raw = trains.get_tickets(a[0][0],a[0][1],date)
                        if not 'route' in raw:
                            print(str(raw))
                            return raw
                        a.append(raw['route'])
                #except:
                #    print(sys.exc_info()[0])
                #    del path_variants[i]
                #    i -= 1
                #    return {'error':sys.exc_info()[0]}

            a = p[0] #first segment
            b = p[1] #second segment 

            print('seg1 paths: ',len(a[2]['paths']),'\nseg2 paths: ',len(b[2]['paths']))
        
            for a_p in a[2]['paths']:
                for b_p in b[2]['paths']:
                    a_segs = a_p['segments']
                    b_segs = b_p['segments']

                    a_arrival = a_segs[len(a_segs)-1]['arrival']
                    b_departure = b_segs[0]['departure']

                    #print(a_arrival,b_departure)

                    if a[1] == 'plane':
                        a_arrival = avia_unify(a_arrival, a_segs[len(a_segs)-1]['destination']['city'])
                        #if a_arrival < 0:

                    else:
                        a_arrival = train_unify(a_arrival)

                    if b[1] == 'plane':
                        b_departure = avia_unify(b_departure, b_segs[0]['origin']['city'])
                        #if b_departure < 0:

                    else:
                        b_departure = train_unify(b_departure)
                        
                    #print(a_arrival,b_departure)

                    if a[1] == 'plane':
                        if search.plane_to_train[0] < b_departure - a_arrival < search.plane_to_train[1]:
                            paths.append({'segments':a_segs + b_segs})
                            print('added')
                    else:
                        if search.train_to_plane[0] < b_departure - a_arrival < search.train_to_plane[1]:
                            paths.append({'segments':a_segs + b_segs})
                            print('added')
            print('paths: ',len(paths))
    except:
        return {"error":'error'}

    paths = sorted(paths, key = lambda k: sum(x['pricing'][0]['price'] for x in k['segments']))

    return {
        'route': {
            'origin' : myutils.find_make_place(origin),
            'destination' : myutils.find_make_place(destination),
            'departure' : date,
            'paths' : paths[:10]
            }
        }
                    

def avia_unify(avia_date_time, city):
    t = avia_date_time[-8:]
    t = int(t[:2]) * 3600 + int(t[3:5]) * 60 + int(t[6:]) - search.timezones[city] * 3600
    #if t < 0:
    #    t += 3600 * 24

    return t / 3600.0

def train_unify(train_date_time):
    t = train_date_time[-8:]

    t = int(t[:2]) * 3600 + int(t[3:5]) * 60 + int(t[6:])
    return t / 3600.0