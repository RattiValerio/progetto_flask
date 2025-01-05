import math
import re
from time import sleep

import requests
from flask import render_template, url_for, Blueprint, request, jsonify

from models.conn import db
from models.models import Request, Response

app = Blueprint('api', __name__)

def get_weather_data(lat, lon):
    api_key = "178b22a70fd63d6738bd6cc84ecde753"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Errore nell'API: {response.status_code}, {response.text}")

def get_weather_and_density(lat, lon):
    weather_data = get_weather_data(lat, lon)
    temperature = weather_data['main']['temp']
    pressure = weather_data['main']['pressure'] * 100
    wind_speed = weather_data['wind']['speed']
    wind_deg = weather_data['wind']['deg']

    density = calculate_air_density(pressure, temperature)

    return {
        'temperature': temperature,
        'pressure': pressure,
        'wind_speed': wind_speed,
        'wind_deg': wind_deg,
        'density': density,
    }

def calculate_air_density(pressure, temperature):
    R = 287.05  # Specific gas constant for dry air in J/(kg·K)
    temperature_kelvin = temperature + 273.15  # Convert temperature from Celsius to Kelvin
    return pressure / (R * temperature_kelvin)  # Apply the ideal gas law to calculate density

def calculate_with_drag(lat, lon, m, v0, angle_vertical, angle_horizontal, alt, air_data, dt=0.01):
    g = 9.81  # Gravitational acceleration
    air_density = float(air_data.get("density") or 1.225)  # Air density (kg/m^3)
    C_r = 0.47  # Resistance coefficient for a sphere
    A = 0.01  # Area frontale del proiettile (m^2)

    # Wind components
    wind_speed = air_data['wind_speed']
    wind_deg = math.radians(air_data['wind_deg'])
    wind_vx = wind_speed * math.cos(angle_horizontal - wind_deg)
    wind_vz = wind_speed * math.sin(angle_horizontal - wind_deg)

    # Initial speeds
    vx = v0 * math.cos(angle_vertical) * math.cos(angle_horizontal)
    vy = v0 * math.sin(angle_vertical)
    vz = v0 * math.cos(angle_vertical) * math.sin(angle_horizontal)

    # Initial position
    x = 0
    y = alt
    z = 0
    t = 0
    max_height = y

    while y > 0:
        print(f"{x},{y},{z}")

        # Obtain terrain altitude
        horizontal_distance = math.sqrt(x**2 + z**2)
        current_lat, current_lon = calculate_new_coordinates(lat, lon, horizontal_distance, math.degrees(angle_horizontal))
        terrain_altitude = float(get_altitude(current_lat, current_lon))

        # Velocity relative to the fluid (wind)
        rel_vx = vx - wind_vx
        rel_vz = vz - wind_vz
        v = math.sqrt(rel_vx ** 2 + vy ** 2 + rel_vz ** 2)

        # Aerodynamic drag force
        # R = 1/2 * CR * DAria * A * v^2
        F_drag = 0.5 * C_r * air_density * A * v ** 2

        # Accelerations
        ax = -F_drag * (rel_vx / v) / m
        ay = -g - F_drag * (vy / v) / m
        az = -F_drag * (rel_vz / v) / m

        # Speed update
        vx += ax * dt
        vy += ay * dt
        vz += az * dt

        # Positions update
        x += vx * dt
        y += vy * dt
        z += vz * dt

        # Update maximum height
        max_height = max(max_height, y)

        # Check if the bullet hit the ground
        if y <= terrain_altitude:
            break

        # Time increment
        t += dt

    # Calculate horizontal distance
    horizontal_distance = math.sqrt(x**2 + z**2)

    return (x, y, z), max_height, horizontal_distance, t

def decimal_to_dms(decimal_coord, coord_type):
    is_negative = decimal_coord < 0  # Determine if the coordinate is negative
    decimal_coord = abs(decimal_coord)  # Work with the absolute value

    # Extract degrees, minutes, and seconds
    degrees = int(decimal_coord)
    minutes = int((decimal_coord - degrees) * 60)
    seconds = (decimal_coord - degrees - minutes / 60) * 3600

    # Determine the directional indicator based on the coordinate type and sign
    if coord_type == 'latitude':
        direction = 'S' if is_negative else 'N'
    elif coord_type == 'longitude':
        direction = 'W' if is_negative else 'E'

    # Return the formatted DMS string with direction
    return f"{degrees}°{minutes}'{seconds:.2f}\" {direction}"

def dms_to_decimal(dms_str):
    deg, minutes, seconds, direction = re.split('[°\'"]', dms_str) # Split the DMS string into components
    return (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (-1 if direction in ['W', 'S'] else 1)

def get_altitude(latitude, longitude):
    url = f"http://192.168.56.10:5000/v1/gebco"
    params = {'locations': f"{latitude},{longitude}"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return str(data['results'][0]['elevation'])
    else:
        raise Exception(f"Errore nell'API: {response.status_code}, {response.text}")

def calculate_new_coordinates(lat, lon, distance, angle):
    R = 6371000  # Earth's radius in meters

    # Convert initial latitude and longitude to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # Compute new latitude in radians
    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance / R) +
        math.cos(lat_rad) * math.sin(distance / R) * math.cos(angle)
    )

    # Compute new longitude in radians
    new_lon_rad = lon_rad + math.atan2(
        math.sin(angle) * math.sin(distance / R) * math.cos(lat_rad),
        math.cos(distance / R) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )

    # Convert the new latitude and longitude back to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)

    return new_lat, new_lon

def calculate_horizontal_distance(x1, z1, x2, z2):
    return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)

def save_request(data):
    new_request = Request(
        latitude=data['latitude'],
        longitude=data['longitude'],
        muzzle_speed=data['muzzle_speed'],
        vertical_angle=data['vertical_angle'],
        horizontal_angle=data['horizontal_angle'],
        projectile_weight=data['projectile_weight'],
        sender=data['sender']
    )
    db.session.add(new_request)
    db.session.commit()
    return new_request.id

def save_response(request_id, response_data):
    new_response = Response(
        request_id=request_id,
        final_position_lat=response_data['final_position']['latitude'],
        final_position_lon=response_data['final_position']['longitude'],
        final_position_alt=response_data['final_position']['altitude'],
        horizontal_distance=response_data['horizontal_distance'],
        max_height=response_data['max_height'],
        max_height_relative=response_data['max_height_relative'],
        flight_time=response_data['flight_time']
    )
    db.session.add(new_response)
    db.session.commit()


@app.route('/calculate/projectile_ballistics', methods=['POST'])
def calculate_projectile_ballistics():
    lat = dms_to_decimal(request.json.get('latitude'))
    lon = dms_to_decimal(request.json.get('longitude'))
    alt = float(get_altitude(lat, lon))
    start_alt = alt

    v0 = request.json.get('muzzle_speed')
    vertical_angle = math.radians(request.json.get('vertical_angle'))
    horizontal_angle = math.radians(request.json.get('horizontal_angle'))
    m = request.json.get('projectile_weight')

    air_data = get_weather_and_density(lat, lon)

    # Calcolo con attrito
    final_position, max_height, horizontal_distance, flight_time = calculate_with_drag(
        lat, lon, m, v0, vertical_angle, horizontal_angle, alt, air_data
    )

    request_id = save_request({
        'latitude': request.json.get('latitude'),
        'longitude': request.json.get('longitude'),
        'muzzle_speed': v0,
        'vertical_angle': request.json.get('vertical_angle'),
        'horizontal_angle': request.json.get('horizontal_angle'),
        'projectile_weight': m,
        'sender': request.remote_addr
    })

    flight_time = int(horizontal_distance/(v0 * math.cos(vertical_angle)))

    # Posizione finale (convertita in coordinate geografiche)
    latf, lonf = calculate_new_coordinates(lat, lon, horizontal_distance, math.degrees(horizontal_angle))

    alt = float(get_altitude(latf, lonf))

    response = {
        'final_position': {
            'latitude': latf,
            'longitude': lonf,
            'altitude': alt,
            'formatted': f"{decimal_to_dms(latf, 'latitude')}, {decimal_to_dms(lonf, 'longitude')}"
        },
        'horizontal_distance': horizontal_distance,
        'max_height': max_height,
        'max_height_relative': max_height - start_alt,
        'flight_time': flight_time,
    }

    save_response(request_id, response)

    return jsonify(response), 201

