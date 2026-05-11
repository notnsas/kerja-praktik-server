from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    jsonify,
    send_from_directory,
)
from app import app
from app.forms import LoginForm
import os
from src.predict_pipeline import PredictPipeline
import pandas as pd
from app import db
from app.models import Hotel, Room
import json

MODEL_DIR = "models/model_12_bulan_v5"
CACHE_PATH = f"{MODEL_DIR}/average_2026.json"

# Initialize
predict_pipeline = PredictPipeline(model_dir=MODEL_DIR)
df = pd.read_csv("data/room_monthly_features_v8.csv")

# Load the 2026 average price cache into memory at startup
try:
    with open(CACHE_PATH, "r") as f:
        # JSON keys are always saved as strings, so {"370150": 450000}
        AVERAGE_2026_CACHE = json.load(f)
    print("✅ 2026 Average Cache loaded into memory.")
except FileNotFoundError:
    print("⚠️ Warning: average_2026.json not found. Run the offline script first.")
    AVERAGE_2026_CACHE = {}


# @app.route("/")
# @app.route("/index")
# def index():
#     # user = {"username": "Nara"}
#     # posts = [
#     #     {"author": {"username": "John"}, "body": "Beatiful day in Portland or sum!"},
#     #     {"author": {"username": "Susan"}, "body": "The avenger so cool sum!"},
#     # ]
#     return render_template("dist/index.html")
# Serve React App
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    dist_dir = os.path.join(app.root_path, "dist")
    print(f"Serving React app from: {dist_dir}, requested path: {path}")

    # If file exists → serve it (JS, CSS, etc)
    if path != "" and os.path.exists(os.path.join(dist_dir, path)):
        return send_from_directory(dist_dir, path)

    # Otherwise → React routing
    return send_from_directory(dist_dir, "index.html")


@app.route("/api/predict", methods=["POST"])
def predict():
    # Initialize for pipeline args
    object = request.get_json()
    room_id = int(object.get("room_id"))
    property_id = int(object.get("property_id"))
    print(f"Received request for room_id: {room_id}, property_id: {property_id}")
    y_pred_dict = {}

    # Predict using pipeline
    # y_pred = predict_pipeline.predict(data=df, room_id=room_id, property_id=property_id)
    y_pred = predict_pipeline.predict(room_id=room_id, property_id=property_id)

    # Making dictionary for each predicted month
    # for idx, pred_value in enumerate(y_pred):
    #     y_pred_dict[f"month_{idx+1}_pred"] = pred_value
    return jsonify(y_pred)


@app.route("/api/hotels", methods=["GET"])
def get_hotels():
    """
    Retrieve a list of all available hotels, ordered alphabetically.
    """
    try:
        # 1. Get the data from the database and sort it A-Z
        hotels = db.session.query(Hotel).order_by(Hotel.name).all()

        # 2. Convert to a list of dictionaries, including ALL the new fields!
        hotels_list = [
            {
                "id": hotel.id,
                "name": hotel.name,
                "description": hotel.description,
                "rating": hotel.rating,
                "image_link": hotel.image_link,
                # 👇 THE NEW COLUMNS 👇
                "maps_link": hotel.maps_link,
                "booking_link": hotel.booking_link,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
            }
            for hotel in hotels
        ]

        # 3. Return the JSON response with a 200 OK status
        return jsonify(hotels_list), 200

    except Exception as e:
        # Catch any database errors so the server doesn't crash silently
        return jsonify({"error": str(e)}), 500


@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    # 1. Check if the frontend sent a ?propertyId= parameter
    property_id = request.args.get("propertyId")

    # 2. Filter the query if the ID exists
    if property_id:
        rooms = db.session.query(Room).filter_by(property_id=property_id).all()
    else:
        rooms = db.session.query(Room).all()  # Fallback to all rooms if no ID provided

    # 3. Convert to list of dictionaries
    rooms_list = [
        {"id": r.id, "name": r.name, "propertyId": r.property_id} for r in rooms
    ]

    return jsonify(rooms_list)


@app.route("/api/average-2026", methods=["GET"])
def get_2026_average():
    # Grab the room ID from the URL (e.g., /api/average-2026?roomId=370150)
    room_id = request.args.get("roomId")

    if not room_id:
        return jsonify({"error": "Missing required parameter: roomId"}), 400

    # Look up the average in our memory cache
    # We convert room_id to a string because JSON dictionary keys are strings
    avg_price = AVERAGE_2026_CACHE.get(str(room_id))

    if avg_price is None:
        return (
            jsonify(
                {
                    "roomId": int(room_id),
                    "year": 2026,
                    "average_price_idr": None,
                    "message": "No historical data found for this room in 2026.",
                }
            ),
            404,
        )

    return jsonify(
        {"roomId": int(room_id), "year": 2026, "average_price_idr": int(avg_price)}
    )
