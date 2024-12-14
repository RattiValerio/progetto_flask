import math
import re

import requests
from flask import render_template, url_for, Blueprint, request, jsonify

app = Blueprint('api', __name__)

def calculate_with_drag(m, v0, angle_vertical, angle_horizontal, alt, dt=0.01):
    g = 9.81  # Accelerazione di gravità
    rho = 1.225  # Densità dell'aria (kg/m^3)
    C_d = 0.47  # Coefficiente di resistenza per una sfera
    A = 0.01  # Area frontale del proiettile (m^2)

    vx = v0 * math.cos(angle_vertical) * math.cos(angle_horizontal)
    vy = v0 * math.sin(angle_vertical)
    vz = v0 * math.cos(angle_vertical) * math.sin(angle_horizontal)

    # Stato iniziale
    x, y, z = 0, alt, 0
    t = 0
    energy_total = 0.5 * m * v0 ** 2 + m * g * alt

    positions = []

    while y >= 0:
        v = math.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        F_drag = 0.5 * C_d * rho * A * v ** 2

        ax = -F_drag * (vx / v) / m
        ay = -g - F_drag * (vy / v) / m
        az = -F_drag * (vz / v) / m

        vx += ax * dt
        vy += ay * dt
        vz += az * dt

        x += vx * dt
        y += vy * dt
        z += vz * dt

        energy_kinetic = 0.5 * m * (vx ** 2 + vy ** 2 + vz ** 2)
        energy_potential = m * g * max(y, 0)
        energy_total = energy_kinetic + energy_potential

        positions.append((x, y, z))

        t += dt

    return positions, energy_total, t


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
    m = request.json.get('projectile_weight')

    positions, final_energy, flight_time = calculate_with_drag(m, v0, vertical_angle, horizontal_angle, alt)

    # Posizione finale
    final_position = positions[-1]
    latf, lonf = calculate_new_coordinates(lat, lon, final_position[0], math.degrees(horizontal_angle))
    yf = final_position[1]  # Altitudine finale

    response = {
        'final_position': {
            'latitude': latf,
            'longitude': lonf,
            'altitude': yf,
            'formatted': f"{decimal_to_dms(latf, 'latitude')}, {decimal_to_dms(lonf, 'longitude')}"
        },
        'flight_time': flight_time,
        'final_energy': final_energy
    }
    return jsonify(response), 201
