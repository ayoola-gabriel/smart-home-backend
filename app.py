import eventlet
eventlet.monkey_patch()

import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*":{"origins":"*"}})
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    )

@app.route("/")
def home():
    return "Server running"

rooms_cache = {}
relay_states_cache = {}

@socketio.on("rooms_response")
def handle_rooms_response(data):
    device_id = data.get("device_id")
    rooms = data.get("rooms_saved")
    rooms_cache[device_id] = rooms
    # print(f"📦 Got rooms from {device_id}: {rooms}")
    
@app.route("/get-rooms/<device_id>")
def get_rooms(device_id):
    # Ask ESP32 for rooms
    socketio.emit("get_rooms", {"request": True}, room=device_id)

    # Wait briefly for ESP32 to respond
    import time
    for _ in range(100):  # wait up to 1s
        if device_id in rooms_cache:
            return jsonify({"rooms_saved": rooms_cache[device_id]})
        time.sleep(0.1)
    
    return jsonify({"error": "device not responding"}), 504

# Event: ESP32 sends relay states back
@socketio.on("relay_states_response")
def handle_relay_states_response(data):
    device_id = data.get("device_id")
    relay_states = data.get("relay_states")
    if not device_id or not relay_states:
        return
    relay_states_cache[device_id] = relay_states
    # print(f"📦 Relay states from {device_id}: {relay_states}")


@app.route("/get-relay-states/<device_id>")
def get_relay_states(device_id):
    socketio.emit("get-relay-states", {"request": True}, room=device_id)

    import time
    # wait briefly for hardware to respond
    for _ in range(100):  # up to 1s
        if device_id in relay_states_cache:
            state_str = relay_states_cache[device_id]
            relay_dict = db_state_to_dict(state_str)
            return jsonify({"relay_states": relay_dict})
        time.sleep(0.1)
    
    return jsonify({"error": "device not responding"}), 504

@app.route("/save-rooms/<device_id>", methods=["POST"])
def save_rooms(device_id):
    data = request.get_json()
    rooms = data.get("rooms", "")
    
    # If rooms is a list, join to comma-separated string
    if isinstance(rooms, list):
        rooms_str = ",".join(rooms)
    else:
        rooms_str = str(rooms)
        
    # print(f"Room Received: {rooms_str}")
    socketio.emit("save_rooms", {"rooms":rooms}, room=device_id)

    return jsonify({"success": True, "rooms_saved": rooms_str})

def db_state_to_dict(state_str):
        return {str(i + 1): (char == '1') for i, char in enumerate(state_str)}

def dict_to_db_state(current_state, updates):
    state_list = list(current_state)
    for key, value in updates.items():
        index = int(key) - 1  # Convert to 0-based index
        state_list[index] = '1' if value else '0'
    return ''.join(state_list)
    
@socketio.on("connect", namespace="/")
def connected():
    device_id = request.args.get("device_id")
    if device_id:
        join_room(device_id)
        # print(f"📡 Device {device_id} joined room {device_id}")
        emit("connected_message",{"data":f"id: {request.sid} is connected"})
    else:
        print("⚠️ Client connected without device_id")
        
@socketio.on("disconnect")
def disconnected():
    """event listener when client disconnects to the server"""
    # print("user disconnected")
    emit("disconnect_message",f"user {request.sid} disconnected",broadcast=True)

@socketio.on("toggle_update")
def handle_toggle_update(data):
    device_id = data.get("device_id")
    updates = data.get("updates", {})
    
    if not device_id or not updates:
        return

    emit("toggle_update", {"updates": updates}, room=device_id)

    
@socketio.on("hardware_data")
def handle_hardware_data(data):
    device_id = data.get("device_id")
    
    if not device_id:
        return
    
    measurements = data['measurements']
    voltage = float(measurements.get('voltage', 0))
    current = float(measurements.get("current", 0))
    total_load = float(measurements.get("total_load", 0))
    frequency = float(measurements.get("frequency", 0))
    temperature = float(measurements.get("temperature", 0))
    status = str(measurements.get("status", ''))
    
    payload = {
            "measurements": {
                "voltage": voltage,
                "current": current,
                "power": total_load,
                "status": status,
                "frequency": frequency,
                "temperature": temperature,
            },
        }
        
    
    emit("hardware_update", payload, room=device_id)
    
@socketio.on("esp32_connected")
def handleESP32_connected(data):
    device_id = request.args.get("device_id")
    if not device_id:
        return
    
    emit("hardware_online", room=device_id)
    
@socketio.on("toggle_ack")
def handle_toggle_ack(data):
    device_id = request.args.get("device_id")
    if not device_id:
        return
    emit("toggle_ack_update", data, room=device_id)
    
if __name__ == "__main__":
        
    socketio.run(app, host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 5000)))