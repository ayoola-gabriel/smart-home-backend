import eventlet
eventlet.monkey_patch()

import os, random
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS


API_KEY = ""
# baseURL = "http://127.0.0.1:5000"
baseURL = "https://smart-home-backend-fy58.onrender.com/"

app = Flask(__name__)
app.config['SECRET_KEY'] = API_KEY
CORS(app, resources={r"/*":{"origins":"*"}})
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    # transport=["websocket"]
    )

"""
# Works locally with .env (sqlite) and on Render (Postgres)
db_uri = os.getenv("DATABASE_URL", "sqlite:///local.db")
# Render still provides postgres:// ...; SQLAlchemy wants postgresql://
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class DeviceStatus(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    relay_states = db.Column(db.String(20))   # e.g., "11001010"
    voltage      = db.Column(db.Float)
    total_load   = db.Column(db.Float)
    status       = db.Column(db.String(100))  # e.g., "OK", "Overload", "Overvoltage"
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)
    saved_rooms = db.Column(db.String(100))
    current = db.Column(db.Float)
    
    def __repr__(self):
        return f"<Voltage={self.voltage}V Load={self.total_load}A>"

class RelayCommand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    relay_states = db.Column(db.String(20), default="00000000") # 8 relays off
    
    def __repr__(self):
        return f"<Relays {self.relay_states}>"
    
class RoomSelected(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rooms_saved = db.Column(db.String(100),
                 default="Living Room,Bedroom,Dining Room,Security"
                            ) # Rooms
    def __repr__(self):
        return f"<Rooms {self.rooms_saved}>"
"""

@app.route("/")
def home():
    return "Server running"

rooms_cache = {}

@socketio.on("rooms_response")
def handle_rooms_response(data):
    device_id = data.get("device_id")
    rooms = data.get("rooms_saved")
    rooms_cache[device_id] = rooms
    print(f"📦 Got rooms from {device_id}: {rooms}")
    
@app.route("/get-rooms/<device_id>")
def get_rooms(device_id):
    # print("Rooms")
    # Ask ESP32 for rooms
    socketio.emit("get_rooms", {"request": True}, room=device_id)

    # Wait briefly for ESP32 to respond
    import time
    for _ in range(10):  # wait up to 1s
        if device_id in rooms_cache:
            return jsonify({"rooms_saved": rooms_cache[device_id]})
        time.sleep(0.1)
    
    return jsonify({"error": "device not responding"}), 504

@app.route("/get-relay-states/<device_id>")
def get_relay_states(device_id):
    socketio.emit("get-relay-states", {"request": True}, room=device_id)
"""
@app.route("/get-rooms")
def get_rooms():
    room_saved = RoomSelected.query.first()
    if not room_saved:
        room_saved = RoomSelected(rooms_saved="Living Room,Bedroom,Dining Room,Attic")
    rooms = room_saved.rooms_saved
    
    return jsonify({"rooms_saved": rooms})
"""

@app.route("/save-rooms/<device_id>", methods=["POST"])
def save_rooms(device_id):
    data = request.get_json()
    rooms = data.get("rooms", "")
    
    # If rooms is a list, join to comma-separated string
    if isinstance(rooms, list):
        rooms_str = ",".join(rooms)
    else:
        rooms_str = str(rooms)
        
    print(f"Room Received: {rooms_str}")
    socketio.emit("save-rooms", {"rooms":rooms}, room=device_id)
    
    """
    room_saved = RoomSelected.query.first()
    if not room_saved:
        room_saved = RoomSelected(rooms_saved="")

    # If rooms is a list, join to comma-separated string
    if isinstance(rooms, list):
        rooms_str = ",".join(rooms)
    else:
        rooms_str = str(rooms)

    print(f"{rooms_str}")
    room_saved.rooms_saved = rooms_str
    db.session.add(room_saved)
    db.session.commit()
    """

    return jsonify({"success": True, "rooms_saved": rooms_str})

"""
#Depreciated
#end-point where hardwares poll to get relay commands
@app.route("/get-commands", methods=["GET"])
def get_commands():
    
    
    
    
    checkDB = DeviceStatus.query.first()
    if not checkDB:
        new_status = DeviceStatus(
        relay_states='00000000',
        voltage=0,
        current=0,
        total_load=0,
        status="",
        timestamp=datetime.now(timezone.utc)
        )
        db.session.add(new_status)
        db.session.commit()
    
    latest = DeviceStatus.query.order_by(DeviceStatus.timestamp.desc()).first()
    if latest:
        relay_states = latest.relay_states
    
    relay_dict = db_state_to_dict(relay_states)
    
    # Fetch last 20 readings for chart
    history = (
        DeviceStatus.query.order_by(DeviceStatus.timestamp.desc())
        .limit(10)
        .all()
    )

    voltage_history = [
        {
            "time": record.timestamp.strftime("%H:%M:%S"),
            "value": round(record.voltage, 2)
        }
        for record in reversed(history)  # oldest first
    ]
    
    current_history = [
        {
            "time": record.timestamp.strftime("%H:%M:%S"),
            "value": round(record.current, 2)
        }
        for record in reversed(history)  # oldest first
    ]

    
    return jsonify({
        "relay_states": relay_dict,
        "voltage_history": voltage_history,
        "current_history": current_history,
            })
            """


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
    # api_key = request.args.get("api_key")
    # if api_key != API_KEY:
    #     print("Unauthorized socket connection attempt")
    #     disconnect()
    # else:
    device_id = request.args.get("device_id")
    if device_id:
        join_room(device_id)
        print(f"📡 Device {device_id} joined room {device_id}")
        # print(request.sid)
        # print("client has connected")
        emit("connected_message",{"data":f"id: {request.sid} is connected"})
    else:
        print("⚠️ Client connected without device_id")
        
@socketio.on("disconnect")
def disconnected():
    """event listener when client disconnects to the server"""
    print("user disconnected")
    emit("disconnect_message",f"user {request.sid} disconnected",broadcast=True)

@socketio.on("toggle_update")
def handle_toggle_update(data):
    device_id = data.get("device_id")
    updates = data.get("updates", {})
    # print(f"Toggle update received: {data}")
    
    if not device_id or not updates:
        return

    """
    # Get current relay command from DB
    command = RelayCommand.query.first()
    if not command:
        command = RelayCommand(relay_states="00000000")
        db.session.add(command)
        db.session.commit()
    
    # Convert current state string and apply updates
    new_state = dict_to_db_state(command.relay_states, updates)
    command.relay_states = new_state
    # print(f"New State: {new_state}")
    db.session.commit()
    """

    # print(f"New relay state: {new_state}")

    # Acknowledge back to clients
    emit("toggle_update", {"updates": updates}, room=device_id)


    
@socketio.on("hardware_data")
def handle_hardware_data(data):
    device_id = request.args.get("device_id")
    
    if not device_id:
        print(f"No ID is request")
        return
    # print(f"📥 Hardware data: {data}")
    measurements = data['measurements']
    # relay = data['relay_states']
    voltage = float(measurements.get('voltage', 0))
    current = float(measurements.get("current", 0))
    total_load = float(measurements.get("total_load", 0))
    frequency = float(measurements.get("frequency", 0))
    temperature = float(measurements.get("temperature", 0))
    status = str(measurements.get("status", ''))
    
    """
    # print(f"FROM HARDWARE -- Relay states: {relay} ")
    # Get relay states from DB (latest)
    relay_command = RelayCommand.query.first()
    relay_states = relay_command.relay_states if relay_command else "00000000"

     # Save to DB
    new_status = DeviceStatus(
        relay_states=relay_states,
        voltage=voltage,
        current=current,
        total_load=total_load,
        status=status,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(new_status)
    db.session.commit()
    
     # ✅ Fetch last 20 readings for chart
    history = (
        DeviceStatus.query.order_by(DeviceStatus.timestamp.desc())
        .limit(10)
        .all()
    )

    voltage_history = [
        {
            "time": record.timestamp.strftime("%H:%M:%S"),
            "value": round(record.voltage, 2)
        }
        for record in reversed(history)  # oldest first
    ]
    
    current_history = [
        {
            "time": record.timestamp.strftime("%H:%M:%S"),
            "value": round(record.current, 2)
        }
        for record in reversed(history)  # oldest first
    ]
    
    # print(f"Current Hisoty: {current_history}")
    """
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
    # device_id = data.get("device_id", "ESP32")
    print(f"✅ Device connected: {device_id} (SID: {request.sid})")
    # print(f"ESP32 connected: {data['device_id']} (SID: {request.sid})")
    emit("hardware_online", room=device_id)
    
@socketio.on("toggle_ack")
def handle_toggle_ack(data):
    device_id = request.args.get("device_id")
    if not device_id:
        return
    print(f"{data}")
    emit("toggle_ack_update", data, room=device_id)
    
if __name__ == "__main__":
    # import os
    
    # app, socketio = create_app()
    
    # with app.app_context():
    #     db.create_all()
    #     print(f"Tables created")
        
    socketio.run(app, host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 5000)))