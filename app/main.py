from fastapi import FastAPI, Depends # Depends might be used by root endpoint
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import aiohttp

# Monkey patch aiohttp.streams.StreamReader to increase the limit for large lines (e.g. base64 images)
# The default limit is 64KB, which is too small for 4K image base64 strings.
# We intercept the __init__ method to force a larger limit.
if hasattr(aiohttp, 'streams') and hasattr(aiohttp.streams, 'StreamReader'):
    _original_stream_reader_init = aiohttp.streams.StreamReader.__init__

    def _patched_stream_reader_init(self, protocol, limit, *args, **kwargs):
        # Force limit to 100MB regardless of what is passed
        new_limit = 100 * 1024 * 1024
        _original_stream_reader_init(self, protocol, new_limit, *args, **kwargs)

    aiohttp.streams.StreamReader.__init__ = _patched_stream_reader_init
    print(f"INFO: Successfully patched aiohttp.streams.StreamReader to enforce 100MB limit.")
else:
    print("WARNING: Could not patch aiohttp.streams.StreamReader. Large images might fail.")

# Local module imports
from auth import get_api_key # Potentially for root endpoint
from credentials_manager import CredentialManager
from express_key_manager import ExpressKeyManager
from location_manager import LocationManager
from vertex_ai_init import init_vertex_ai

# Routers
from routes import models_api
from routes import chat_api
from routes import admin_api

app = FastAPI(title="OpenAI to Gemini Adapter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

credential_manager = CredentialManager()
app.state.credential_manager = credential_manager # Store manager on app state

express_key_manager = ExpressKeyManager()
app.state.express_key_manager = express_key_manager # Store express key manager on app state

location_manager = LocationManager()
app.state.location_manager = location_manager # Store location manager on app state

# Include API routers
app.include_router(models_api.router)
app.include_router(chat_api.router)
app.include_router(admin_api.router)

@app.on_event("startup")
async def startup_event():
    # Check SA credentials availability
    sa_credentials_available = await init_vertex_ai(credential_manager, location_manager)
    sa_count = credential_manager.get_total_credentials() if sa_credentials_available else 0
    
    # Check Express API keys availability
    express_keys_count = express_key_manager.get_total_keys()
    
    # Print detailed status
    print(f"INFO: SA credentials loaded: {sa_count}")
    print(f"INFO: Express API keys loaded: {express_keys_count}")
    print(f"INFO: Total authentication methods available: {(1 if sa_count > 0 else 0) + (1 if express_keys_count > 0 else 0)}")
    
    # Determine overall status
    if sa_count > 0 or express_keys_count > 0:
        print("INFO: Vertex AI authentication initialization completed successfully. At least one authentication method is available.")
        if sa_count == 0:
            print("INFO: No SA credentials found, but Express API keys are available for authentication.")
        elif express_keys_count == 0:
            print("INFO: No Express API keys found, but SA credentials are available for authentication.")
    else:
        print("ERROR: Failed to initialize any authentication method. Both SA credentials and Express API keys are missing. API will fail.")

@app.get("/")
async def root():
    return RedirectResponse(url="/admin")
