import os
from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager, ClimateRequestOptions, Vehicle
from hyundai_kia_connect_api.exceptions import AuthenticationError

app = Flask(__name__)

# Get credentials from environment variables
USERNAME = os.environ.get('KIA_USERNAME')
PASSWORD = os.environ.get('KIA_PASSWORD')
PIN = os.environ.get('KIA_PIN')

if USERNAME is None or PASSWORD is None or PIN is None:
    raise ValueError("Missing credentials! Check your environment variables.")

# Initialize Vehicle Manager
vehicle_manager = VehicleManager(
    region=3,  # North America region
    brand=1,   # KIA brand
    username=USERNAME,
    password=PASSWORD,
    pin=str(PIN)
)

# Refresh the token and update vehicle states
try:
    print("Attempting to authenticate and refresh token...")
    vehicle_manager.check_and_refresh_token()
    print("Token refreshed successfully.")

    print("Updating vehicle states...")
    vehicle_manager.update_all_vehicles_with_cached_state()
    print(f"Connected! Found {len(vehicle_manager.vehicles)} vehicle(s).")
    
    for vid, vehicle in vehicle_manager.vehicles.items():
        print(f"Vehicle ID: {vid}, Name: {vehicle.name}, Model: {vehicle.model}, Battery: {vehicle.ev_battery_percentage}")
        
except AuthenticationError as e:
    print(f"Failed to authenticate: {e}")
    exit(1)
except Exception as e:
    print(f"Unexpected error during initialization: {e}")
    exit(1)


# Secret key for security - moved to environment variables
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Missing SECRET_KEY environment variable.")

# Dynamically fetch the first vehicle ID if VEHICLE_ID is not set
VEHICLE_ID = os.environ.get("VEHICLE_ID")
if not VEHICLE_ID:
    if not vehicle_manager.vehicles:
        raise ValueError("No vehicles found in the account. Please ensure your Kia account has at least one vehicle.")
    # Fetch the first vehicle ID
    VEHICLE_ID = next(iter(vehicle_manager.vehicles.keys()))
    print(f"No VEHICLE_ID provided. Using the first vehicle found: {VEHICLE_ID}")

# Log incoming requests
@app.before_request
def log_request_info():
    print(f"Incoming request: {request.method} {request.url}")

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({"status": "Welcome to the Kia Vehicle Control API"}), 200

# List vehicles endpoint
@app.route('/list_vehicles', methods=['GET'])
def list_vehicles():
    print("Received request to /list_vehicles")

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        print("Refreshing vehicle states...")
        vehicle_manager.update_all_vehicles_with_cached_state()

        vehicles = vehicle_manager.vehicles
        print(f"Vehicles data: {vehicles}")  # Log the vehicles data

        if not vehicles:
            print("No vehicles found in the account")
            return jsonify({"error": "No vehicles found"}), 404

        # Iterate over the dictionary values (Vehicle objects)
        vehicle_list = [
            {
                "name": v.name,
                "id": v.id,
                "model": v.model,
                "year": v.year
            

            }
            for v in vehicles.values()  # Use .values() to get the Vehicle objects
        ]

        if not vehicle_list:
            print("No valid vehicles found in the account")
            return jsonify({"error": "No valid vehicles found"}), 404

        print(f"Returning vehicle list: {vehicle_list}")
        return jsonify({"status": "Success", "vehicles": vehicle_list}), 200
    except Exception as e:
        print(f"Error in /list_vehicles: {e}")
        return jsonify({"error": str(e)}), 500

# Start climate endpoint
@app.route('/start_climate', methods=['POST'])
def start_climate():
    print("Received request to /start_climate")

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        print("Refreshing vehicle states...")
        vehicle_manager.update_all_vehicles_with_cached_state()

        # Create ClimateRequestOptions object
        climate_options = ClimateRequestOptions(
            set_temp=65,  # Set temperature in Fahrenheit
            duration=15,   # Duration in minutes
       #     defrost=False,
            heating=0,
            steering_wheel=0,        # 1 = on, 0 = off
         #  front_left_seat=8        doesn't work at this time 4/4/25
        )

        # Start climate control using the VehicleManager's start_climate method
        result = vehicle_manager.start_climate(VEHICLE_ID, climate_options)
        print(f"Start climate result: {result}")

        return jsonify({"status": "Climate started", "result": result}), 200
    except Exception as e:
        print(f"Error in /start_climate: {e}")
        return jsonify({"error": str(e)}), 500

# Stop climate endpoint
@app.route('/stop_climate', methods=['POST'])
def stop_climate():
    print("Received request to /stop_climate")

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        print("Refreshing vehicle states...")
        vehicle_manager.update_all_vehicles_with_cached_state()

        # Stop climate control using the VehicleManager's stop_climate method
        result = vehicle_manager.stop_climate(VEHICLE_ID)
        print(f"Stop climate result: {result}")

        return jsonify({"status": "Climate stopped", "result": result}), 200
    except Exception as e:
        print(f"Error in /stop_climate: {e}")
        return jsonify({"error": str(e)}), 500

# Unlock car endpoint
@app.route('/unlock_car', methods=['POST'])
def unlock_car():
    print("Received request to /unlock_car")

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        print("Refreshing vehicle states...")
        vehicle_manager.update_all_vehicles_with_cached_state()

        # Unlock the vehicle using the VehicleManager's unlock method
        result = vehicle_manager.unlock(VEHICLE_ID)
        print(f"Unlock result: {result}")

        return jsonify({"status": "Car unlocked", "result": result}), 200
    except Exception as e:
        print(f"Error in /unlock_car: {e}")
        return jsonify({"error": str(e)}), 500

# Lock car endpoint
@app.route('/lock_car', methods=['POST'])
def lock_car():
    print("Received request to /lock_car")

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        print("Refreshing vehicle states...")
        vehicle_manager.update_all_vehicles_with_cached_state()

        # Lock the vehicle using the VehicleManager's lock method
        result = vehicle_manager.lock(VEHICLE_ID)
        print(f"Lock result: {result}")

        return jsonify({"status": "Car locked", "result": result}), 200
    except Exception as e:
        print(f"Error in /lock_car: {e}")
        return jsonify({"error": str(e)}), 500


# get_vehicle_status endpoint

# Global cache
last_valid_status = {
    "battery_percentage": None,
    "range_miles": None,
    "model": None
}

@app.route("/get_vehicle_status", methods=["GET"])
def get_vehicle_status():
    global last_valid_status

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        vehicle_manager.check_and_force_update_vehicles(force_refresh_interval=0)
        vehicle = vehicle_manager.vehicles[VEHICLE_ID]

        battery = vehicle.ev_battery_percentage
        model = vehicle.model
        range_miles = vehicle.ev_driving_range
        charging = vehicle.ev_battery_is_charging
        charge_minutes = getattr(vehicle, "ev_estimated_current_charge_duration", None)

        # Cache valid range
        if range_miles and range_miles > 0:
            last_valid_status = {
                "battery_percentage": battery,
                "range_miles": range_miles,
                "model": model
            }

        if range_miles == 0:
            range_miles = last_valid_status.get("range_miles")

        return jsonify({
            "battery_percentage": battery,
            "range_miles": range_miles,
            "model": model,
            "charging": charging,
            "charge_minutes": charge_minutes  # ⏱️ Add this
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# get Attributes about car status endpoint

@app.route('/debug_vehicle', methods=['GET'])
def debug_vehicle():
    try:
        vehicle = vehicle_manager.vehicles[VEHICLE_ID]
        vehicle_manager.check_and_force_update_vehicles(force_refresh_interval=0)

        attributes = dir(vehicle)
        return jsonify({'attributes': attributes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Battery Status Endpoint
@app.route('/battery_status', methods=['GET'])
def battery_status():
    print("Received request to /battery_status")

    if request.headers.get("Authorization") != SECRET_KEY:
        print("Unauthorized request: Missing or incorrect Authorization header")
        return jsonify({"error": "Unauthorized"}), 403

    try:
        print("Refreshing vehicle states...")
        vehicle_manager.update_all_vehicles_with_cached_state()


        # Fetch the battery percentage (State of Charge - SOC)
        vehicle = vehicle_manager.vehicles.get(VEHICLE_ID)
        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        battery_percentage = vehicle.ev_battery_percentage  # EV battery SOC
        print(f"Battery SOC: {battery_percentage}%")

        return jsonify({"status": "Success", "battery_percentage": battery_percentage}), 200
    except Exception as e:
        print(f"Error in /battery_status: {e}")
        return jsonify({"error": str(e)}), 500

# climate options Endpoint
@app.route("/climate_options_debug", methods=["GET"])
def climate_options_debug():
    try:
        opts = ClimateRequestOptions()
        return jsonify({
            "available_attrs": dir(opts),
            "doc": ClimateRequestOptions.__doc__
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    print("Starting Kia Vehicle Control API...")
    app.run(host="0.0.0.0", port=8080)
