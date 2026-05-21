from flask import Flask, request, jsonify
from api.database import supabase

app = Flask(__name__)

# CREATE
@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.json
    response = supabase.table("Users").insert(data).execute()
    return jsonify(response.data), 201

# READ (All)
@app.route('/api/items', methods=['GET'])
def get_items():
    response = supabase.table("Users").select("*").execute()
    return jsonify(response.data), 200

# READ (Single)
@app.route('/api/items/<item_id>', methods=['GET'])
def get_item(item_id):
    response = supabase.table("Users").select("*").eq("id", item_id).execute()
    if not response.data:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(response.data[0]), 200

# UPDATE
@app.route('/api/items/<item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    response = supabase.table("Users").update(data).eq("id", item_id).execute()
    return jsonify(response.data), 200

# DELETE
@app.route('/api/items/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    response = supabase.table("Users").delete().eq("id", item_id).execute()
    return jsonify({"message": "Item deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
