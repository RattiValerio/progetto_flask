import math
import re
import os
from time import sleep

import requests
from flask import render_template, url_for, Blueprint, request, jsonify

from models.conn import db
from models.models import Request, Response

app = Blueprint('api', __name__)


def get_weather_data(lat, lon):
    """
    Gets weather data from the OpenWeatherMap API

    @param lat: latitude of the position
    @param lon: longitude of the position
    @return: a JSON object containing the weather data
    """

    api_key = os.getenv('OPENWEATHER_API_KEY')
    url = f"{os.getenv('OPENWEATHER_URL')}/{os.getenv('OPENWEATHER_VERSION')}/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Errore nell'API: {response.status_code}, {response.text}")


def get_weather_and_density(lat, lon):
    """
    Gets weather data from the OpenWeatherMap API and calculates the air density

    @param lat: latitude of the position
    @param lon: longitude of the position
    @return: a dictionary containing the weather data and the calculated air density
    """
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
    """
    Calculates the air density using the ideal gas law

    @param pressure: atmospheric pressure in pascals
    @param temperature: air temperature in degrees Celsius
    @return: air density in kg/m^3
    """
    R = 287.05  # Specific gas constant for dry air in J/(kg·K)
    temperature_kelvin = temperature + 273.15  # Convert temperature from Celsius to Kelvin
    return pressure / (R * temperature_kelvin)  # Apply the ideal gas law to calculate density


def calculate_with_drag(lat, lon, m, v0, angle_vertical, angle_horizontal, alt, air_data, dt=0.01):
    """
    Calculates the trajectory of a projectile considering atmospheric drag


    @param lat: The latitude of the starting position
    @param lon: The longitude of the starting position
    @param m: The mass of the projectile
    @param v0: The muzzle speed of the projectile
    @param angle_vertical: The angle of departure (relative to the horizontal)
    @param angle_horizontal: The angle of departure (relative to the North)
    @param alt: The starting altitude
    @param air_data: A dictionary containing the air density, wind speed and direction
    @param dt: The time step for the simulation
    @return: The final position of the projectile, the maximum height reached,
             the horizontal distance traveled, and the flight time.
    """
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
        print(f"X: {x:.2f} | Y: {x:.2f} | Z: {x:.2f}")

        # Obtain terrain altitude
        horizontal_distance = math.sqrt(x ** 2 + z ** 2)
        current_lat, current_lon = calculate_new_coordinates(lat, lon, horizontal_distance,
                                                             math.degrees(angle_horizontal))
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
    horizontal_distance = math.sqrt(x ** 2 + z ** 2)

    return (x, y, z), max_height, horizontal_distance, t


def decimal_to_dms(decimal_coord, coord_type):
    """
    Converts a decimal coordinate to a string in the Degrees-Minutes-Seconds format


    @param decimal_coord: The decimal coordinate to be converted
    @param coord_type: The type of coordinate (latitude or longitude)
    @return: The formatted DMS string with direction
    """
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
    """
    Converts a string in the Degrees-Minutes-Seconds format to a decimal coordinate.

    @param dms_str: The DMS string to be converted
    @return: The decimal representation of the coordinate
    """
    deg, minutes, seconds, direction = re.split('[°\'"]', dms_str)  # Split the DMS string into components
    return (float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)) * (-1 if direction in ['W', 'S'] else 1)


def get_altitude(latitude, longitude):
    """
    Gets the altitude of a given position from the Elevation API

    @param latitude: The latitude of the position
    @param longitude: The longitude of the position
    @return: The altitude of the position
    """
    url = f"{os.getenv('ELEVATION_API_URL')}/{os.getenv('ELEVATION_DATASET')}"
    params = {'locations': f"{latitude},{longitude}"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return str(data['results'][0]['elevation'])
    else:
        raise Exception(f"Errore nell'API: {response.status_code}, {response.text}")


def calculate_new_coordinates(lat, lon, distance, angle):
    """Calculates the new latitude and longitude given an initial position, a distance, and an angle.

    @param lat: The initial latitude
    @param lon: The initial longitude
    @param distance: The distance to move
    @param angle: The angle to move in
    @return: The new latitude and longitude
    """
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
    """
    Calculates the horizontal distance between two points in a 2D plane.

    @param x1: The x-coordinate of the first point
    @param z1: The z-coordinate of the first point
    @param x2: The x-coordinate of the second point
    @param z2: The z-coordinate of the second point
    @return: The horizontal distance between the two points
    """
    return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)


def save_request(data):
    """
    Saves a new request to the database.

    @param data: A dictionary containing request details such as latitude,
                 longitude, muzzle speed, vertical angle, horizontal angle,
                 projectile weight, and sender.
    @return: The ID of the newly created request.
    """
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
    """
    Saves a new response to the database.

    @param request_id: The ID of the request that the response belongs to.
    @param response_data: A dictionary containing response details such as
                          final position, horizontal distance, maximum height,
                          maximum height relative to the starting altitude,
                          and flight time.
    """
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
    """
    Calculates the trajectory of a projectile considering atmospheric drag.

    @param lat: The latitude of the starting position
    @param lon: The longitude of the starting position
    @param alt: The starting altitude
    @param v0: The muzzle speed of the projectile
    @param vertical_angle: The vertical angle of departure
    @param horizontal_angle: The horizontal angle of departure
    @param m: The mass of the projectile
    @param air_data: A dictionary containing air density, wind speed and direction
    @return: The final position of the projectile, the maximum height reached, the horizontal distance traveled, and the flight time.
    """
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

    flight_time = int(horizontal_distance / (v0 * math.cos(vertical_angle)))

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

    return jsonify(response), 200


@app.route('/get/requests', methods=['GET'])
def get_requests():
    """
    Retrieves all requests from the database.

    @return: A JSON response containing a list of all requests.
    """
    api_requests = Request.query.all()
    return jsonify([r.to_dict() for r in api_requests]), 200


@app.route('/get/request/<request_id>', methods=['GET'])
def get_request_by_id(request_id):
    """
    Retrieves a specific request from the database by its ID.

    @param request_id: The ID of the request to retrieve.
    @return: A JSON response containing the request details.
    """
    api_requests = Request.query.filter_by(id=request_id).all()
    return jsonify([r.to_dict() for r in api_requests]), 200
