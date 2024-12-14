import math
import re

import requests
from flask import render_template, url_for, Blueprint, request, jsonify

app = Blueprint('api', __name__)


def decimal_to_dms(decimal_coord, coord_type):
    is_negative = decimal_coord < 0
    decimal_coord = abs(decimal_coord)

    degrees = int(decimal_coord)
    minutes = int((decimal_coord - degrees) * 60)
    seconds = (decimal_coord - degrees - minutes / 60) * 3600

    if coord_type == 'latitude':
        direction = 'S' if is_negative else 'N'
    elif coord_type == 'longitude':
        direction = 'W' if is_negative else 'E'

    return f"{degrees}°{minutes}'{seconds:.2f}\"{direction}"


def dms_to_decimal(dms_str):
    deg, minutes, seconds, direction = re.split('[°\'"]', dms_str)
    return (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (-1 if direction in ['W', 'S'] else 1)

def get_altitude(latitude, longitude):
    url = f"https://api.open-elevation.com/api/v1/lookup"
    params = {'locations': f"{latitude},{longitude}"}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['results'][0]['elevation']
    else:
        raise Exception(f"Errore nell'API: {response.status_code}, {response.text}")

def calculate_new_coordinates(lat, lon, distance, angle):
    R = 6371000  # Earth radius (meters)

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance / R) +
        math.cos(lat_rad) * math.sin(distance / R) * math.cos(angle)
    )

    new_lon_rad = lon_rad + math.atan2(
        math.sin(angle) * math.sin(distance / R) * math.cos(lat_rad),
        math.cos(distance / R) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )

    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)

    return new_lat, new_lon

@app.route('/calculate/projectile_ballistics', methods=['POST'])
def calculate_projectile_ballistics():
    lat = dms_to_decimal(request.json.get('latitude'))
    lon = dms_to_decimal(request.json.get('longitude'))
    alt = request.json.get('altitude')

    v0 = request.json.get('muzzle_speed')
    vertical_angle = math.radians(request.json.get('vertical_angle'))
    horizontal_angle = math.radians(request.json.get('horizontal_angle'))

    g = 9.81

    v0x = v0 * math.cos(vertical_angle) * math.cos(horizontal_angle)
    v0y = v0 * math.sin(vertical_angle)
    v0z = v0 * math.cos(vertical_angle) * math.sin(horizontal_angle)

    tf = (2 * v0y) / g

    ymax = alt + (v0y * v0y) / (2 * g)

    range = (v0 ** 2 * math.sin(2 * vertical_angle)) / g

    latf, lonf = calculate_new_coordinates(lat, lon, range, math.degrees(horizontal_angle))
    yf = get_altitude(latf, lonf)

    response = {
        'final_position': {
            'latitude': latf,
            'longitude': lonf,
            'altitude': yf,
            'formatted': f"{decimal_to_dms(latf, 'latitude')}, {decimal_to_dms(lonf, 'longitude')}"
        },
        'range': range,
        'fly_time': tf,
        'max_height': ymax,
    }
    return jsonify(response), 201


# def calculate_projectile_ballistics():
#     lat = dms_to_decimal(request.json.get('latitude'))
#     lon = dms_to_decimal(request.json.get('longitude'))
#     alt = request.json.get('altitude')
#
#     v0 = request.json.get('muzzle_speed')
#
#     vertical_angle = math.radians(request.json.get('vertical_angle'))
#
#     horizontal_angle = math.radians(request.json.get('horizontal_angle'))
#
#     m = request.json.get('projectile_weight')
#
#     g = 9.81
#
#     # x = v0x * t
#     # y = v0y *t - 1/2 * g * t ^ 2
#
#     # Velocità iniziali
#     # v0x = v0 * cos(angolo_verticale) * cos(angolo_orizzontale)
#     # v0z = v0 * cos(angolo_verticale) * sin(angolo_orizzontale)
#     # v0y = v0 * sin(angolo_verticale)
#
#     v0x = v0 * math.cos(vertical_angle) * math.cos(horizontal_angle)
#     v0z = v0 * math.cos(vertical_angle) * math.sin(horizontal_angle)
#     v0y = v0 * math.sin(vertical_angle)
#
#     # Tempo di volo
#     # y0 + v0y * t - 1/2 * g * t ^ 2
#     # tf = (2 * v0y) / g
#
#     tf = (2 * v0y) / g
#
#     # Posizione finale
#     # xf = x0 + v0 * cos(angolo_verticale) * cos(angolo_orizzontale) * tf
#     # zf = z0 + z0 * cos(angolo_verticale) * sin(angolo_orizzontale) * tf
#     # yf = y0 ???
#
#     xf = lat + v0x * tf
#     zf = lon + v0z * tf
#     yf = get_altitude(lat, lon)
#
#     # Altezza massima
#     # ymax = y0 + ((v0 * sin(angolo_verticale)) ^ 2) / 2 * g
#
#     ymax = alt + (v0y * v0y) / (2 * g)
#
#     latf, lonf = calculate_new_coordinates(lat, lon, tf, horizontal_angle)
#
#     # Range
#     # range = (v0^2 * sin(2 * angolo_verticale)) / g
#     range = 0
#     if math.sin(vertical_angle) != 1:
#         range = (float(v0) * float(v0) * math.sin(2 * vertical_angle)) / g
#
#     response = {
#         'final_position': {
#             'latitude': latf,
#             'longitude': lonf,
#             'altitude': yf,
#             'formatted': f"{decimal_to_dms(latf, 'latitude')}, {decimal_to_dms(lonf, 'longitude')}"
#         },
#         'range': range,
#         'fly_time': tf,
#         'max_height': ymax,
#     }
#     return jsonify(response), 201
