import os
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import config as app_config

router = APIRouter()

# Path to config files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOCATIONS_FILE = os.path.join(BASE_DIR, "locations.json")

class ConfigUpdate(BaseModel):
    password: str
    config_json: str

def get_admin_html():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Vertex Adapter</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 20px auto; padding: 0 20px; }
        .container { display: none; }
        .login-container { text-align: center; margin-top: 100px; }
        textarea { width: 100%; height: 400px; font-family: monospace; margin-bottom: 10px; }
        button { padding: 10px 20px; cursor: pointer; background-color: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover { background-color: #0056b3; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        select { width: 100%; padding: 8px; }
        .alert { padding: 10px; margin-bottom: 10px; border-radius: 4px; display: none; }
        .alert.success { background-color: #d4edda; color: #155724; }
        .alert.error { background-color: #f8d7da; color: #721c24; }
        .section { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
    </style>
</head>
<body>

<div id="login-view" class="login-container">
    <h2>Admin Login</h2>
    <input type="password" id="api-key-input" placeholder="Enter API Key" style="padding: 10px; width: 200px;">
    <button onclick="login()">Login</button>
    <p id="login-error" style="color: red; display: none;">Invalid API Key</p>
</div>

<div id="admin-view" class="container">
    <h2>Configuration Manager</h2>
    <div id="status-msg" class="alert"></div>

    <div class="section">
        <h3>Location Settings</h3>
        <div class="form-group">
            <label for="location-select">Default Location:</label>
            <select id="location-select"></select>
        </div>
        <div class="form-group">
            <label>
                <input type="checkbox" id="auto-switch-check"> Auto Switch Location
            </label>
            <small style="display: block; color: #666; margin-top: 5px;">
                If unchecked, the system will strictly use the selected location.
            </small>
        </div>
    </div>

    <div class="section">
        <h3>Raw Config (JSON)</h3>
        <textarea id="config-editor"></textarea>
    </div>

    <button onclick="saveConfig()">Save Changes</button>
</div>

<script>
    let currentConfig = {};
    let apiKey = localStorage.getItem('admin_api_key') || '';

    async function fetchConfig() {
        const response = await fetch('/admin/data?password=' + encodeURIComponent(apiKey));
        if (response.status === 401) {
            logout();
            return;
        }
        const data = await response.json();
        currentConfig = data.config;
        
        // Populate Location Dropdown
        const locSelect = document.getElementById('location-select');
        locSelect.innerHTML = '';
        data.locations.forEach(loc => {
            const opt = document.createElement('option');
            opt.value = loc;
            opt.textContent = loc;
            locSelect.appendChild(opt);
        });

        // Set values
        if (currentConfig.DEFAULT_LOCATION) {
            locSelect.value = currentConfig.DEFAULT_LOCATION;
        }
        document.getElementById('auto-switch-check').checked = currentConfig.AUTO_SWITCH_LOCATION !== false; // Default true
        
        // Set JSON editor
        document.getElementById('config-editor').value = JSON.stringify(currentConfig, null, 4);
        
        showAdmin();
    }

    function login() {
        const inputKey = document.getElementById('api-key-input').value;
        apiKey = inputKey;
        fetchConfig().catch(() => {
            document.getElementById('login-error').style.display = 'block';
        });
    }

    function logout() {
        document.getElementById('login-view').style.display = 'block';
        document.getElementById('admin-view').style.display = 'none';
        localStorage.removeItem('admin_api_key');
    }

    function showAdmin() {
        document.getElementById('login-view').style.display = 'none';
        document.getElementById('admin-view').style.display = 'block';
        localStorage.setItem('admin_api_key', apiKey);
    }

    // Sync UI controls with JSON editor
    function updateJsonFromUI() {
        try {
            const currentJson = JSON.parse(document.getElementById('config-editor').value);
            currentJson.DEFAULT_LOCATION = document.getElementById('location-select').value;
            currentJson.AUTO_SWITCH_LOCATION = document.getElementById('auto-switch-check').checked;
            document.getElementById('config-editor').value = JSON.stringify(currentJson, null, 4);
            return currentJson;
        } catch (e) {
            alert("Invalid JSON in editor!");
            return null;
        }
    }

    document.getElementById('location-select').addEventListener('change', updateJsonFromUI);
    document.getElementById('auto-switch-check').addEventListener('change', updateJsonFromUI);

    async function saveConfig() {
        const newConfig = updateJsonFromUI();
        if (!newConfig) return;

        const statusDiv = document.getElementById('status-msg');
        statusDiv.style.display = 'none';

        try {
            const response = await fetch('/admin/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    password: apiKey,
                    config_json: JSON.stringify(newConfig, null, 4)
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                statusDiv.textContent = result.message || 'Configuration saved successfully!';
                statusDiv.className = 'alert success';
            } else {
                statusDiv.textContent = 'Error: ' + result.detail;
                statusDiv.className = 'alert error';
            }
            statusDiv.style.display = 'block';
        } catch (e) {
            statusDiv.textContent = 'Network Error: ' + e;
            statusDiv.className = 'alert error';
            statusDiv.style.display = 'block';
        }
    }

    // Auto-login check
    if (apiKey) {
        fetchConfig();
    }
</script>
</body>
</html>
    """

@router.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return get_admin_html()

@router.get("/admin/data")
async def get_admin_data(password: str):
    # Simple auth check against current loaded config
    if password != app_config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    # Read fresh config file
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception:
        config = {}

    try:
        with open(LOCATIONS_FILE, 'r', encoding='utf-8') as f:
            locations = json.load(f)
    except Exception:
        locations = []

    return JSONResponse({
        "config": config,
        "locations": locations
    })

@router.post("/admin/config")
async def update_config(request: Request, data: ConfigUpdate):
    # Auth check
    # Note: We compare against the currently loaded app_config.API_KEY
    # If the user changes the API_KEY in the config, they will need to use the new one next time.
    if data.password != app_config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        # Validate JSON
        new_config = json.loads(data.config_json)
        
        # Write to file
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=4)
        
        # Hot-reload Location Manager settings if possible
        if hasattr(request.app.state, 'location_manager'):
            lm = request.app.state.location_manager
            
            # Since properties are now dynamic, we don't set them manually.
            # But we might want to reset the current index if the default changed
            # and we are currently using the old default (or just force a switch).
            
            if 'DEFAULT_LOCATION' in new_config:
                new_default = new_config['DEFAULT_LOCATION']
                # lm.default_location is now a read-only property, so we don't set it.
                # But we can update the current index if needed.
                if new_default in lm.locations:
                    # Only switch if the current location index was pointing to something else
                    # or just force it to the new default.
                    lm.current_location_index = lm.locations.index(new_default)
                    print(f"INFO: Admin updated location settings. Current location switched to: {new_default}")

        return {"status": "success", "message": "Config updated. Settings applied immediately."}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))