# Projectile Ballistics API

This project provides an API for simulating projectile ballistics considering various environmental and physical factors, such as air resistance, wind speed, and altitude. It integrates with external services for weather data and terrain elevation.

---

## Features

- **Weather Integration**: Fetches weather data (temperature, pressure, wind speed, etc.) for the specified location using the OpenWeather API.
- **Projectile Simulation**: Simulates projectile motion with air resistance and wind effects.
- **Altitude Adjustment**: Accounts for terrain elevation at the starting and ending coordinates using an elevation API.
- **Data Persistence**: Saves requests and responses to a database for tracking calculations.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Set up a virtual environment**:
   Make sure you have Python 3.8+ installed. Create a virtual environment and install the dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the root directory and add the following variables:
   ```env
   SQLALCHEMY_DATABASE_URI=sqlite:///ballistics.db
   OPENWEATHER_API_KEY=your_openweather_api_key
   OPENWEATHER_URL=https://api.openweathermap.org/data
   OPENWEATHER_VERSION=2.5
   ELEVATION_API_URLhttp://192.168.56.10:5000/v1
   ELEVATION_DATASET=gebco
   ```

4. **Optional: Set up an elevation API (if you don’t have one)**:
   - Navigate to the `elevation_vm` directory:
     ```bash
     cd elevation_vm
     ```
   - Use **Vagrant** to spin up a virtual machine and configure a local elevation API:
     ```bash
     vagrant up
     ```
     This will create a virtual machine with the **GEBCO** dataset and start the **OpenTopodata** service.

   - Once the setup is complete, the service will be available at `http://192.168.56.10:5000`.

5. **Run the application**:
   Go back to the project root and start the Flask server:
   ```bash
   flask run
   ```

---

## API Endpoints

### `POST /calculate/projectile_ballistics`
Simulates the trajectory of a projectile given input parameters.

#### Request Body
```json
{
  "latitude": "40°45'0\" N",
  "longitude": "73°59'0\" W",
  "muzzle_speed": 300,
  "vertical_angle": 45,
  "horizontal_angle": 0,
  "projectile_weight": 5
}
```
- **latitude**: Starting latitude in DMS format.
- **longitude**: Starting longitude in DMS format.
- **muzzle_speed**: Initial speed of the projectile in m/s.
- **vertical_angle**: Vertical launch angle in degrees.
- **horizontal_angle**: Horizontal launch angle in degrees.
- **projectile_weight**: Projectile weight in kilograms.

#### Response Body
```json
{
  "final_position": {
    "latitude": 40.748817,
    "longitude": -73.985428,
    "altitude": 15.0,
    "formatted": "40°44'55.74\" N, 73°59'7.54\" W"
  },
  "horizontal_distance": 1500.0,
  "max_height": 200.0,
  "max_height_relative": 185.0,
  "flight_time": 30
}
```
- **final_position**: Final geographic coordinates and altitude of the projectile.
- **horizontal_distance**: Total horizontal distance traveled in meters.
- **max_height**: Maximum altitude reached in meters.
- **max_height_relative**: Maximum height relative to the starting altitude.
- **flight_time**: Total flight time in seconds.

---

## Key Functions

### 1. `get_weather_data(lat, lon)`
Fetches weather data for the given latitude and longitude.

### 2. `calculate_air_density(pressure, temperature)`
Calculates air density using the ideal gas law.

### 3. `calculate_with_drag(lat, lon, m, v0, angle_vertical, angle_horizontal, alt, air_data, dt=0.01)`
Simulates projectile motion considering air drag and wind.

### 4. `calculate_new_coordinates(lat, lon, distance, angle)`
Calculates new coordinates based on a starting point, distance, and bearing angle.

### 5. `save_request(data)` and `save_response(request_id, response_data)`
Saves request and response data to the database.

---

## Requirements
- Python 3.7+
- Flask
- Requests
- SQLAlchemy

---

## Notes
- Ensure all required environment variables are set before running the application.
- Adjust the `dt` parameter in `calculate_with_drag` for higher accuracy or performance trade-offs.

---

## License
This project is licensed under the MIT License.

