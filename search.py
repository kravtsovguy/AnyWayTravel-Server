# -*- coding: utf-8 -*-
import pandas as pd
import json
import codecs
import numpy as np

train_to_plane = [4,8]
plane_to_train = [3,8]
trains = codecs.open('trains_cache.json', 'r', 'utf-8')
avias = codecs.open('avia_cache.json', 'r', 'utf-8')
data_tr = json.loads(trains.read())
data_av = json.loads(avias.read())
cities = []
size = 0
for data in data_av:
    city = data['origin']['city']
    cities.append(city)
    paths = data['paths']
    for path in paths:
        segments = path['segments']
        if len(segments) > 1:
            continue
        size += 1

avias_norm = pd.DataFrame(columns=['time_dep', 'time_ar', 'city_dep', 'city_ar', 'price'], index=range(size))
size = 0
for data in data_av:
    city = data['origin']['city']
    cities.append(city)
    paths = data['paths']
    for path in paths:
        segments = path['segments']
        if len(segments) > 1:
            continue
        size += 1

trains_norm = pd.DataFrame(columns=['time_dep', 'time_ar', 'city_dep', 'city_ar', 'price'], index=range(size))

cities = np.unique(cities)
timezone = [7, -1, 0, 4, 3, 0, 2, 2]
timezones = dict(zip(cities, timezone))
index = 0
for data in data_av:
    city_or = data['origin']['city']
    city_dest = data['destination']['city']
    paths = data['paths']
    for path in paths:
        segments = path['segments']
        if len(segments) > 1:
            continue
        segment = segments[0]
        time_dep = segment['departure'][-8:]

        time_ar = segment['arrival'][-8:]

        time_dep = int(time_dep[:2]) * 3600 + int(time_dep[3:5]) * 60 + int(time_dep[6:]) - timezones[city_or] * 3600
        if time_dep < 0:
            time_dep += 3600 * 24
        time_dep %= 24 * 3600
        time_ar = int(time_ar[:2]) * 3600 + int(time_ar[3:5]) * 60 + int(time_ar[6:]) - timezones[city_dest] * 3600
        if time_ar < 0:
            time_ar += 3600 * 24
        time_ar %= 24 * 3600
        new_row = [time_dep, time_ar, city_or, city_dest, segment['pricing'][0]['price']]
        avias_norm.iloc[index] = new_row
        index += 1
index = 0
for data in data_tr:
    city_or = data['origin']['city']
    city_dest = data['destination']['city']
    paths = data['paths']
    for path in paths:
        segments = path['segments']
        if len(segments) > 1:
            continue
        segment = segments[0]
        time_dep = segment['departure'][-8:]

        time_ar = segment['arrival'][-8:]

        time_dep = int(time_dep[:2]) * 3600 + int(time_dep[3:5]) * 60 + int(time_dep[6:])
        time_ar = int(time_ar[:2]) * 3600 + int(time_ar[3:5]) * 60 + int(time_ar[6:])
        new_row = [time_dep, time_ar, city_or, city_dest, segment['pricing'][0]['price']]
        trains_norm.iloc[index] = new_row
        index += 1


def get_paths(origin, destination):
    variants_1 = {}
    variants_2 = {}
    for city in cities:
        if city == origin or destination == city:
            continue
        airs = avias_norm[avias_norm.city_dep == origin]

        airs = airs[airs.city_ar == city]
        trains = trains_norm[trains_norm.city_dep == city]

        trains = trains[trains.city_ar == destination]
        price = 10000000
        for i in range(airs.shape[0]):
            time_ar = airs.time_ar.values[i]
            for j in range(trains.shape[0]):
                time_dep = trains.time_dep.values[j]
                if (time_dep > time_ar and 3600 * plane_to_train[0]< time_dep - time_ar <= plane_to_train[1] * 3600) or (
                                time_dep < time_ar and (24-plane_to_train[1]) * 3600 <= time_ar - time_dep <= (24-plane_to_train[0]) * 3600):
                    price = min(price, airs.price.values[i] + trains.price.values[j])
        variants_1[city] = price

    for city in cities:
        if city == origin or destination == city:
            continue
        trains = trains_norm[trains_norm.city_dep == origin]

        trains = trains[trains.city_ar == city]
        airs = avias_norm[avias_norm.city_dep == city]

        airs = airs[airs.city_ar == destination]

        price = 10000000
        for i in range(trains.shape[0]):
            time_ar = trains.time_ar.values[i]
            for j in range(airs.shape[0]):
                time_dep = airs.time_dep.values[j]
                if (time_dep > time_ar and 3600 * train_to_plane[0]< time_dep - time_ar <= train_to_plane[1] * 3600) or (
                                time_dep < time_ar and (24-train_to_plane[1]) * 3600 <= time_ar - time_dep <= (24-train_to_plane[0]) * 3600):
                    price = min(price, airs.price.values[j] + trains.price.values[i])

        variants_2[city] = price
    variants_1 = sorted(variants_1.items(), key=lambda t: t[1])
    variants_2 = sorted(variants_2.items(), key=lambda t: t[1])

    itog = []
    if variants_1[0][1]<1000000:
        itog.append([[[origin, variants_1[0][0]],'plane'],[[variants_1[0][0], destination],'train']])
    if variants_1[1][1]<1000000:
        itog.append([[[origin, variants_1[1][0]],'plane'],[[variants_1[1][0], destination],'train']])
    if variants_2[0][1]<1000000:
        itog.append([[[origin, variants_2[0][0]],'train'],[[variants_2[0][0], destination],'plane']])
    if variants_2[1][1]<1000000:
        itog.append([[[origin, variants_2[1][0]],'train'],[[variants_2[1][0], destination],'plane']])
    return itog

