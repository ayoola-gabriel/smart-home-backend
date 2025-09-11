# Smart Home Dashboard

A Flask-based smart home backend for monitoring and controlling hardware relays, tracking voltage/current, and managing room configurations. Real-time communication is enabled via Socket.IO.

## Features

- Real-time hardware data updates (voltage, current, temperature, etc.)
- Relay control and status tracking (8 relays)
- Room management (save and retrieve room names)
- REST API endpoints for frontend/backend integration
- WebSocket events for live updates
- SQLite/PostgreSQL database support

## Project Structure

```
app.py                # Main Flask app and Socket.IO server
hardwaresimu.py       # Hardware simulator for testing relay/data updates
init_db.py            # Script to initialize the database tables
requirements.txt      # Python dependencies
instance/local.db     # SQLite database (created at runtime)
.gitignore            # Ignore instance and venv folders
```

## Setup

1. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

2. **Initialize the database:**

   ```sh
   python init_db.py
   ```

3. **Run the server:**

   ```sh
   python app.py
   ```

4. *(Optional)* **Run the hardware simulator:**

   ```sh
   python hardwaresimu.py
   ```

## API Endpoints

- `GET /get-rooms` — Retrieve saved room names
- `POST /save-rooms` — Save room names (JSON: `{ "rooms": [...] }`)
- `GET /get-commands` — Get current relay states and measurement history

## WebSocket Events

- `toggle_update` — Update relay states
- `hardware_data` — Send hardware measurements
- `esp32_connected` — Notify when hardware connects
- `toggle_ack` — Acknowledge relay toggle

## Database Models

- **DeviceStatus**: Stores relay states, voltage, current, load, status, timestamp
- **RelayCommand**: Stores current relay states
- **RoomSelected**: Stores saved room names

## Notes

- Default database is SQLite (`instance/local.db`). For production, set `DATABASE_URL` to a PostgreSQL URI.
- Hardware simulator (`hardwaresimu.py`) mimics ESP32 device behavior for development/testing.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.