import os
import json

# Load config.json if it exists
# Get the directory where config.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

config_data = {}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        print(f"Loaded configuration from {CONFIG_FILE}")
    except Exception as e:
        print(f"Warning: Error loading config.json: {e}")

def get_conf(key, default=None):
    """Get configuration from config.json or environment variables."""
    # Priority: config.json > environment variable > default
    val = config_data.get(key)
    if val is not None:
        if isinstance(val, bool):
            return "true" if val else "false"
        return str(val)
    return os.environ.get(key, default)

# Default password if not set in environment
DEFAULT_PASSWORD = "123456"

# Get password from environment variable or use default
API_KEY = get_conf("API_KEY", DEFAULT_PASSWORD)

# HuggingFace Authentication Settings
HUGGINGFACE = get_conf("HUGGINGFACE", "false").lower() == "true"
HUGGINGFACE_API_KEY = get_conf("HUGGINGFACE_API_KEY", "") # Default to empty string, auth logic will verify if HF_MODE is true and this key is needed

# Directory for service account credential files
CREDENTIALS_DIR = get_conf("CREDENTIALS_DIR", "/app/credentials")

# JSON string for service account credentials (can be one or multiple comma-separated)
GOOGLE_CREDENTIALS_JSON_STR = get_conf("GOOGLE_CREDENTIALS_JSON")

# API Key for Vertex Express Mode
raw_vertex_keys = get_conf("VERTEX_EXPRESS_API_KEY")
if raw_vertex_keys:
    VERTEX_EXPRESS_API_KEY_VAL = [key.strip() for key in raw_vertex_keys.split(',') if key.strip()]
else:
    VERTEX_EXPRESS_API_KEY_VAL = []

# Fake streaming settings for debugging/testing
FAKE_STREAMING_ENABLED = get_conf("FAKE_STREAMING", "false").lower() == "true"
FAKE_STREAMING_INTERVAL_SECONDS = float(get_conf("FAKE_STREAMING_INTERVAL", "1.0"))

# URL for the remote JSON file containing model lists
MODELS_CONFIG_URL = get_conf("MODELS_CONFIG_URL", "https://raw.githubusercontent.com/gzzhongqi/vertex2openai/refs/heads/main/vertexModels.json")

# Constant for the Vertex reasoning tag
VERTEX_REASONING_TAG = "vertex_think_tag"

# Round-robin credential selection strategy
ROUNDROBIN = get_conf("ROUNDROBIN", "false").lower() == "true"

# Safety score display setting
SAFETY_SCORE = get_conf("SAFETY_SCORE", "false").lower() == "true"
# Validation logic moved to app/auth.py

# Proxy settings
PROXY_URL = get_conf("PROXY_URL")
SSL_CERT_FILE = get_conf("SSL_CERT_FILE")

# Cloudflare R2 Image Storage Settings
R2_ENABLED = get_conf("R2_ENABLED", "false").lower() == "true"
R2_ACCOUNT_ID = get_conf("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = get_conf("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = get_conf("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = get_conf("R2_BUCKET_NAME", "")
R2_PUBLIC_URL = get_conf("R2_PUBLIC_URL", "")  # e.g., https://your-bucket.r2.dev

# Location Switching Settings
AUTO_SWITCH_LOCATION = get_conf("AUTO_SWITCH_LOCATION", "true").lower() == "true"
MAX_RETRIES_BEFORE_SWITCH = int(get_conf("MAX_RETRIES_BEFORE_SWITCH", "1"))
DEFAULT_LOCATION = get_conf("DEFAULT_LOCATION", "asia-southeast1")