from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from gemini_parser import parse_receipt
from db_helpers import init_db, add_item, get_items, update_item_storage, get_expiration_timestamp

app = Flask(__name__)
CORS(app)
init_db()

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

@app.route('/item/<user_id>', methods = ['GET'])
def fetch_user_items(user_id):
    items = get_items(user_id);
    if not items: return jsonify({"Error":"Missing items"}), 400
    return jsonify(items)

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


if __name__ == "__main__":
    app.run()



