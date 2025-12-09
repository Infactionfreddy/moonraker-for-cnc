# Moonraker CNC REST API Documentation

**Version**: 1.0  
**Date**: 9. Dezember 2025  
**Module**: `cnc_extended_api.py`

## Overview

Moonraker CNC REST API provides comprehensive HTTP endpoints for controlling all CNC M-Codes remotely. This enables integration with:
- Web interfaces (Mainsail, Fluidd)
- Custom control panels
- External automation systems
- Mobile apps
- Remote monitoring tools

All endpoints follow REST principles with JSON request/response format.

---

## Base URL

```
http://<moonraker-ip>:7125/server/cnc/
```

---

## Endpoints

### 1. Tool Change (M6)

**Endpoint**: `POST /server/cnc/tool_change`

**Description**: Execute tool change operation with M6

**Request Body**:
```json
{
  "tool": 5,          // Tool number (T parameter)
  "manual": true,     // Manual (true) or automatic (false)
  "pause": true       // Pause for operator confirmation
}
```

**Response**:
```json
{
  "result": "success",
  "tool": 5,
  "manual": true,
  "commands": ["M0", "T5", "M117 Insert Tool T5 and resume"]
}
```

**M-Code Equivalent**: `M6 T5`

---

### 2. CNC Status

**Endpoint**: `GET /server/cnc/status`

**Description**: Get comprehensive CNC system status

**Response**:
```json
{
  "result": "success",
  "status": {
    "optional_stop_enabled": true,
    "spindle_running": true,
    "spindle_direction": 1,
    "spindle_speed": 1000,
    "coolant_mist": false,
    "coolant_flood": true,
    "feed_override_enabled": true,
    "spindle_override_enabled": true,
    "adaptive_feed_enabled": false,
    "feed_stop_enabled": false
  }
}
```

---

### 3. Coolant Control (M7, M8, M9)

#### Get Coolant Status

**Endpoint**: `GET /server/cnc/coolant`

**Response**:
```json
{
  "result": "success",
  "coolant_mist": false,
  "coolant_flood": true
}
```

#### Control Coolant

**Endpoint**: `POST /server/cnc/coolant`

**Request Body**:
```json
{
  "mist": true,   // M7 (mist on) or M9 (off)
  "flood": false  // M8 (flood on) or M9 (off)
}
```

**Response**:
```json
{
  "result": "success",
  "mist": true,
  "flood": false
}
```

**M-Code Equivalent**: `M7`, `M8`, `M9`

---

### 4. Spindle Control (M3, M4, M5)

#### Get Spindle Status

**Endpoint**: `GET /server/cnc/spindle`

**Response**:
```json
{
  "result": "success",
  "spindle_running": true,
  "spindle_direction": 1,  // 1=CW, -1=CCW, 0=stopped
  "spindle_speed": 1000
}
```

#### Control Spindle

**Endpoint**: `POST /server/cnc/spindle`

**Request Body**:
```json
{
  "enable": true,        // true=start, false=stop (M5)
  "direction": "cw",     // "cw" (M3) or "ccw" (M4)
  "speed": 1000          // RPM (S parameter)
}
```

**Response**:
```json
{
  "result": "success",
  "enable": true,
  "direction": "cw",
  "speed": 1000
}
```

**M-Code Equivalent**: `M3 S1000`, `M4 S1000`, `M5`

---

### 5. Pallet Change (M60)

**Endpoint**: `POST /server/cnc/pallet_change`

**Description**: Initiate pallet change with pause for operator action

**Request Body**:
```json
{
  "pause": true  // Pause for operator (default: true)
}
```

**Response**:
```json
{
  "result": "success",
  "command": "M60",
  "pause": true,
  "message": "Pallet change initiated - Exchange pallet and resume"
}
```

**M-Code Equivalent**: `M60`

---

### 6. Digital I/O (M62-M66)

#### Get Digital I/O Status

**Endpoint**: `GET /server/cnc/digital_io`

**Response**:
```json
{
  "result": "success",
  "message": "Digital I/O status retrieved"
}
```

#### Set Digital Output (M62-M65)

**Endpoint**: `POST /server/cnc/digital_io`

**Request Body**:
```json
{
  "pin": 0,               // Pin number (P parameter)
  "value": true,          // true=ON, false=OFF
  "synchronized": false   // false=immediate (M64/M65), true=synced (M62/M63)
}
```

**Response**:
```json
{
  "result": "success",
  "command": "M64 P0",
  "pin": 0,
  "value": true,
  "synchronized": false
}
```

**M-Code Equivalent**: 
- `M62 P0` - Digital output ON, synchronized with motion
- `M63 P0` - Digital output OFF, synchronized with motion
- `M64 P0` - Digital output ON, immediate
- `M65 P0` - Digital output OFF, immediate

#### Wait on Input (M66)

**Endpoint**: `POST /server/cnc/digital_io`

**Request Body**:
```json
{
  "action": "wait",
  "pin": 0,              // Pin number
  "mode": 3,             // 0=IMMEDIATE, 1=RISE, 2=FALL, 3=HIGH, 4=LOW
  "timeout": 5.0,        // Timeout in seconds
  "analog": false        // true for analog input (E parameter)
}
```

**Response**:
```json
{
  "result": "success",
  "command": "M66 P0 L3 Q5.0",
  "message": "Waiting on digital input 0"
}
```

**M-Code Equivalent**: `M66 P0 L3 Q5.0`

---

### 7. Analog I/O (M67, M68)

#### Get Analog I/O Status

**Endpoint**: `GET /server/cnc/analog_io`

**Response**:
```json
{
  "result": "success",
  "message": "Analog I/O status retrieved"
}
```

#### Set Analog Output

**Endpoint**: `POST /server/cnc/analog_io`

**Request Body**:
```json
{
  "pin": 0,               // Pin number (E parameter)
  "value": 7.5,           // Analog value (Q parameter)
  "synchronized": false   // false=immediate (M68), true=synced (M67)
}
```

**Response**:
```json
{
  "result": "success",
  "command": "M68 E0 Q7.5",
  "pin": 0,
  "value": 7.5,
  "synchronized": false
}
```

**M-Code Equivalent**:
- `M67 E0 Q7.5` - Analog output, synchronized with motion
- `M68 E0 Q7.5` - Analog output, immediate

---

### 8. Subroutines (M98, M99)

**Endpoint**: `POST /server/cnc/subroutine`

**Description**: Call or return from Fanuc-style subroutines

#### Call Subroutine (M98)

**Request Body**:
```json
{
  "action": "call",
  "program": 100,    // Program number (O-word number)
  "repeats": 3       // Number of times to repeat (L parameter)
}
```

**Response**:
```json
{
  "result": "success",
  "command": "M98 P100 L3",
  "action": "call",
  "program": 100,
  "repeats": 3,
  "message": "Called subroutine O100 (3 times)"
}
```

**M-Code Equivalent**: `M98 P100 L3`

#### Return from Subroutine (M99)

**Request Body**:
```json
{
  "action": "return"
}
```

**Response**:
```json
{
  "result": "success",
  "command": "M99",
  "action": "return",
  "message": "Returned from subroutine"
}
```

**M-Code Equivalent**: `M99`

---

### 9. Modal State Management (M70-M73)

**Endpoint**: `GET/POST/DELETE /server/cnc/modal_state`

**Description**: Save, restore, and manage modal machine state

#### Get Modal State Status

**Method**: `GET /server/cnc/modal_state`

**Response**:
```json
{
  "result": "success",
  "message": "Modal state tracking active"
}
```

#### Save/Restore Modal State

**Method**: `POST /server/cnc/modal_state`

**Request Body**:
```json
{
  "action": "save"  // "save" (M70), "restore" (M72), "invalidate" (M71), "auto_save" (M73)
}
```

**Response**:
```json
{
  "result": "success",
  "action": "save",
  "command": "M70"
}
```

**M-Code Equivalent**:
- `M70` - Save modal state
- `M71` - Invalidate saved state
- `M72` - Restore modal state
- `M73` - Save with auto-restore

#### Clear All Modal States

**Method**: `DELETE /server/cnc/modal_state`

**Response**:
```json
{
  "result": "success",
  "message": "All modal states cleared"
}
```

---

## Error Handling

All endpoints return error responses in the following format:

```json
{
  "result": "error",
  "message": "Error description here"
}
```

**Common Error Codes**:
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Endpoint not found
- `500 Internal Server Error` - Klippy not connected or execution error

---

## Authentication

Moonraker REST API supports multiple authentication methods:
- **API Key**: Pass in `X-Api-Key` header
- **Token Auth**: Use OAuth tokens
- **Trusted Clients**: Configure in `moonraker.conf`

Example with API Key:
```bash
curl -X POST http://moonraker:7125/server/cnc/tool_change \
  -H "X-Api-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tool": 5, "manual": true}'
```

---

## Usage Examples

### Python Example

```python
import requests

MOONRAKER_URL = "http://192.168.1.100:7125"

# Start spindle
response = requests.post(
    f"{MOONRAKER_URL}/server/cnc/spindle",
    json={"enable": True, "direction": "cw", "speed": 1000}
)
print(response.json())

# Set analog output
response = requests.post(
    f"{MOONRAKER_URL}/server/cnc/analog_io",
    json={"pin": 0, "value": 7.5, "synchronized": False}
)
print(response.json())

# Tool change
response = requests.post(
    f"{MOONRAKER_URL}/server/cnc/tool_change",
    json={"tool": 3, "manual": True, "pause": True}
)
print(response.json())
```

### JavaScript Example

```javascript
const MOONRAKER_URL = "http://192.168.1.100:7125";

// Start spindle CW at 1000 RPM
fetch(`${MOONRAKER_URL}/server/cnc/spindle`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    enable: true,
    direction: 'cw',
    speed: 1000
  })
})
.then(res => res.json())
.then(data => console.log(data));

// Digital output ON (immediate)
fetch(`${MOONRAKER_URL}/server/cnc/digital_io`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    pin: 0,
    value: true,
    synchronized: false
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL Examples

```bash
# Get CNC status
curl http://moonraker:7125/server/cnc/status

# Start spindle
curl -X POST http://moonraker:7125/server/cnc/spindle \
  -H "Content-Type: application/json" \
  -d '{"enable": true, "direction": "cw", "speed": 1000}'

# Tool change
curl -X POST http://moonraker:7125/server/cnc/tool_change \
  -H "Content-Type: application/json" \
  -d '{"tool": 5, "manual": true, "pause": true}'

# Digital output
curl -X POST http://moonraker:7125/server/cnc/digital_io \
  -H "Content-Type: application/json" \
  -d '{"pin": 0, "value": true, "synchronized": false}'

# Analog output
curl -X POST http://moonraker:7125/server/cnc/analog_io \
  -H "Content-Type: application/json" \
  -d '{"pin": 0, "value": 7.5, "synchronized": false}'

# Call subroutine
curl -X POST http://moonraker:7125/server/cnc/subroutine \
  -H "Content-Type: application/json" \
  -d '{"action": "call", "program": 100, "repeats": 3}'
```

---

## WebSocket Integration

Moonraker also supports WebSocket connections for real-time updates. Subscribe to CNC state changes:

```javascript
const ws = new WebSocket('ws://moonraker:7125/websocket');

ws.onopen = () => {
  // Subscribe to CNC status updates
  ws.send(JSON.stringify({
    jsonrpc: "2.0",
    method: "printer.objects.subscribe",
    params: {
      objects: {
        cnc_extended_m_codes: null
      }
    },
    id: 1
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('CNC Status Update:', data);
};
```

---

## Configuration

Enable CNC REST API in `moonraker.conf`:

```ini
[cnc_extended_api]
# Enable CNC M-Code REST API endpoints
# No additional configuration required
```

---

## Compatibility

- **Moonraker Version**: 0.8.0+
- **Klipper Version**: Requires `cnc_extended_m_codes` module
- **Protocols**: HTTP/1.1, WebSocket
- **Format**: JSON
- **Authentication**: API Key, Token, Trusted Clients

---

## Complete M-Code Coverage

All LinuxCNC M-Codes are accessible via REST API:

| Category | M-Codes | Endpoint |
|----------|---------|----------|
| Tool Change | M6 | `/tool_change` |
| Spindle | M3, M4, M5, M19 | `/spindle` |
| Coolant | M7, M8, M9 | `/coolant` |
| Pallet | M60 | `/pallet_change` |
| Digital I/O | M62-M66 | `/digital_io` |
| Analog I/O | M67-M68 | `/analog_io` |
| Subroutines | M98-M99 | `/subroutine` |
| Modal State | M70-M73 | `/modal_state` |
| Status | All | `/status` |

---

## License

**Copyright © 2025 Moonraker CNC Project**  
**License**: GNU GPLv3

---

## Support

- **Issues**: https://github.com/klipper-cnc/moonraker/issues
- **Documentation**: https://moonraker-cnc.readthedocs.io
- **Community**: https://discord.gg/klipper-cnc
