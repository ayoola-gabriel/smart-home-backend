import requests
import random
import time
import socketio
# from app import baseURL

baseURL = "https://smart-home-backend-fy58.onrender.com/"

sio = socketio.Client()

# Relay state in binary string (8 switches)
relay_state = list("00000000")  # Start with all OFF

# Generate random measurement values
def generate_measurements():
    voltage=round(random.uniform(220, 240), 2)  # Simulate 220-240V
    current=round(random.uniform(0.5, 120.0), 2)  # Simulate 0.5-5A    
    total_load = voltage * current
    status='Good'
    if(voltage>240):
        status='Overvoltage'
    elif(voltage<150):
        status = 'Undervoltage'
    elif((total_load/1000)>33):
        status = 'Overload'

    
    return {
        "voltage":voltage,  # Simulate 220-240V
        "current": current,
        "temperature":round(random.uniform(25, 50), 1),  # Simulate 25-50°C
        "frequency":round(random.uniform(49,50)),
        "total_load":total_load,
        "status":status
    }

# Event: Connection established
@sio.event
def connect():
    print("Hardware Connected to server")
    # Optionally send an initial handshake message
    sio.emit("esp32_connected", {'device_id': "HomeBoard1v00"})

# Event: Disconnected
@sio.event
def disconnect():
    print("Hardware Disconnected from server")
    
# Event: Receive toggle updates from frontend
@sio.on("toggle_update")
def handle_toggle_update(data):
    global relay_state
    switch_state = data.get('updates')
    key = list(switch_state.keys())[0]
    state = switch_state[key]

    switch = int(key) - 1
      
    relay_state[switch] = "1" if state else "0"
    relay_states = ''.join(relay_state)
    
    sleep_time = round(random.uniform(0,3),0)
    time.sleep(sleep_time)
    
    # Send acknowledgement back to the server
    # sio.emit("toggle_ack", 
    #          {"switch": switch + 1, 
    #           "state": state,
    #           "relay_states":relay_states
    #           })
    sio.emit("toggle_ack", 
             {"updates":{key: state},
              "relay_states":relay_states})
    # print(f"✅ Updated relay_state: {''.join(relay_state)}")
    
# Periodic data sender
def send_hardware_data():
    while True:
        measurements = generate_measurements()
                
        sio.emit("hardware_data", {
            "measurements": measurements,
            "relay_states": relay_state
        })
        # print(f"📡 Sent hardware_update: {measurements}, relay_state: {''.join(relay_state)}")
        
        time.sleep(10)  # Every 5 seconds   

# Connect to the server
sio.connect(baseURL)

# Start sending hardware data
send_hardware_data()

# Keep the script running
sio.wait()
    