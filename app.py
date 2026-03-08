from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from gemini_parser import parse_receipt
from db_helpers import init_db, add_item, get_items, update_item_storage, get_expiration_timestamp
import requests
import numpy as np
import cv2
import io
from ultralytics import YOLO

app = Flask(__name__)
CORS(app)
init_db()

# Initialize YOLO model globally
model = YOLO('yolov8n.pt')

@app.route('/parse-receipt', methods = ['POST'])
def handle_parse_receipt():
    image_file = request.files['image']
    if not image_file: return jsonify({"Error": "Missing image file"}), 400

    image_bytes = image_file.read()
    receipt_info = parse_receipt(image_bytes)
    return jsonify(receipt_info)

@app.route('/add-item', methods = ['POST'])
def handle_add_item():    
    data = request.get_json()
    if not data: return jsonify({"Error" : "Missing data"}), 400

    userID = data.get('user_id')
    itemData = data.get('item_data')
    if not userID or not itemData: return jsonify({"Error":"Missing required fields"}), 400

    success = add_item(userID, itemData)

    if success: return jsonify({"status" : "success"})
    else: return jsonify({"Error":"Failed adding item"}), 400

@app.route('/items', methods = ['GET'])
def fetch_user_items():
    user_id = request.args.get('user_id')
    if not user_id: return jsonify({"Error": "Missing user_id parameter"}), 400

    items = get_items(user_id)
    # Even if items is empty, it shouldn't return 400 unless there's a db error. We can return an empty list.
    if items is None: return jsonify({"Error":"Error fetching items"}), 400
    return jsonify({"status": "success", "items": items})

@app.route('/update-storage', methods = ['POST'])
def handle_updated_storage():
    data = request.get_json()
    if not data: return jsonify({"Error":"Missing data"}), 400

    item_id = data.get('item_id')
    item_name = data.get('item_name')
    new_storage = data.get('new_storage')
    if not item_id or not item_name or not new_storage: return jsonify({"Error":"Missing required fields"}), 400

    new_expiration_timestamp = get_expiration_timestamp(item_id, new_storage)
    
    success = update_item_storage(item_id, new_storage, new_expiration_timestamp) 

    if success:
        return jsonify({"status" : "success"})

@app.route('/annotate-image', methods=['POST'])
def handle_annotate_image():
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({"Error": "Missing image_url"}), 400

    try:
        # Download image
        response = requests.get(image_url)
        response.raise_for_status()

        # Convert to numpy array and decode
        nparr = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Run YOLO inference
        results = model(img)
        
        # Plot bounding boxes onto the image array
        annotated_img = results[0].plot()

        # Encode back to JPEG
        _, buffer = cv2.imencode('.jpg', annotated_img)
        byte_io = io.BytesIO(buffer)

        # Send raw bytes back
        return send_file(byte_io, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"Error": str(e)}), 500

if __name__ == "__main__":
    app.run()

