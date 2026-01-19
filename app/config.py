import os
import json
import time

# Config file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

class ConfigLoader:
    def __init__(self):
        self._cache = {}
        self._last_mtime = 0
        self.config_file = CONFIG_FILE

    def _reload_if_needed(self):
        try:
            if not os.path.exists(self.config_file):
                return

            current_mtime = os.stat(self.config_file).st_mtime
            if current_mtime > self._last_mtime:
                # File changed, reload
                print(f"DEBUG: Reloading configuration from {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                self._last_mtime = current_mtime
        except Exception as e:
            print(f"ERROR: Failed to reload config: {e}")

    def get(self, key, default=None):
        self._reload_if_needed()
        val = self._cache.get(key)
        if val is not None:
            return val
        return default

    def get_bool(self, key, default=False):
        val = self.get(key)
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        return str(val).lower() == "true"

    def get_int(self, key, default=0):
        val = self.get(key)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default
            
    def get_float(self, key, default=0.0):
        val = self.get(key)
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

_loader = ConfigLoader()

# Default values mapping
DEFAULTS = {
    "API_KEY": "123456",
    "CREDENTIALS_DIR": "/app/credentials",
    "MODELS_CONFIG_URL": "https://raw.githubusercontent.com/gzzhongqi/vertex2openai/refs/heads/main/vertexModels.json",
    "FAKE_STREAMING_INTERVAL": 1.0,
    "MAX_RETRIES_BEFORE_SWITCH": 1,
    "DEFAULT_LOCATION": "asia-southeast1"
}

def __getattr__(name):
    # Dynamic property access
    if name == "VERTEX_REASONING_TAG":
        return "vertex_think_tag"
    
    if name == "VERTEX_EXPRESS_API_KEY_VAL":
        raw_keys = _loader.get("VERTEX_EXPRESS_API_KEY", "")
        if isinstance(raw_keys, str):
            return [key.strip() for key in raw_keys.split(',') if key.strip()]
        return []

    # Handle simple mappings
    # Map legacy variable names to JSON keys if they are identical
    # Special handling for boolean conversions based on variable naming conventions or explicit lists
    
    bool_keys = [
        "HUGGINGFACE", "FAKE_STREAMING_ENABLED", "ROUNDROBIN", 
        "SAFETY_SCORE", "R2_ENABLED", "AUTO_SWITCH_LOCATION"
    ]
    
    # Mapping from variable name to JSON key (if different)
    key_map = {
        "GOOGLE_CREDENTIALS_JSON_STR": "GOOGLE_CREDENTIALS_JSON",
        "FAKE_STREAMING_ENABLED": "FAKE_STREAMING",
        "FAKE_STREAMING_INTERVAL_SECONDS": "FAKE_STREAMING_INTERVAL"
    }
    
    json_key = key_map.get(name, name)
    
    if name in bool_keys or json_key in bool_keys:
        # It's a boolean config
        return _loader.get_bool(json_key, False)
    
    if name == "FAKE_STREAMING_INTERVAL_SECONDS":
        return _loader.get_float(json_key, 1.0)
        
    if name == "MAX_RETRIES_BEFORE_SWITCH":
        return _loader.get_int(json_key, 1)

    # Default string/generic getter
    val = _loader.get(json_key, DEFAULTS.get(name))
    
    # Special handling for PROXY_URL: check env vars if not in config
    if name == "PROXY_URL" and not val:
        val = os.environ.get("HTTPS_PROXY") or os.environ.get("PROXY_URL")
        
    return val

# Expose these for explicit imports if needed, though __getattr__ handles them
# We don't define them here to force __getattr__ to be called