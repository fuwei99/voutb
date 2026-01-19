import json
import os
from typing import List, Optional
import config as app_config

class LocationManager:
    def __init__(self):
        self.locations: List[str] = []
        self.current_location_index: int = 0
        self.consecutive_429_count: int = 0
        # Remove local caching of config values
        
        self._load_locations()
        self._set_initial_location()

    @property
    def auto_switch_enabled(self) -> bool:
        return app_config.AUTO_SWITCH_LOCATION

    @property
    def max_retries_before_switch(self) -> int:
        return app_config.MAX_RETRIES_BEFORE_SWITCH

    @property
    def default_location(self) -> str:
        return app_config.DEFAULT_LOCATION

    def _load_locations(self):
        """Load locations from locations.json"""
        try:
            locations_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locations.json")
            if os.path.exists(locations_file):
                with open(locations_file, 'r', encoding='utf-8') as f:
                    self.locations = json.load(f)
                print(f"INFO: Loaded {len(self.locations)} locations from {locations_file}")
            else:
                print(f"WARNING: locations.json not found at {locations_file}. Using default location only.")
                self.locations = [self.default_location]
        except Exception as e:
            print(f"ERROR: Failed to load locations.json: {e}. Using default location only.")
            self.locations = [self.default_location]

    def _set_initial_location(self):
        """Set the initial location index based on DEFAULT_LOCATION"""
        if self.default_location in self.locations:
            self.current_location_index = self.locations.index(self.default_location)
        else:
            print(f"WARNING: DEFAULT_LOCATION '{self.default_location}' not found in loaded locations. Using first available location.")
            self.current_location_index = 0
        print(f"INFO: Initial location set to: {self.get_current_location()}")

    def get_current_location(self) -> str:
        """Return the current location string"""
        if not self.locations:
            return "global" # Fallback
        return self.locations[self.current_location_index]

    def report_error(self, status_code: int):
        """Report an error status code. If 429, increment counter and potentially switch location."""
        # Debug print
        # print(f"DEBUG: report_error called with status {status_code}. Auto-switch enabled: {self.auto_switch_enabled}")

        if not self.auto_switch_enabled:
            return

        if status_code == 429:
            self.consecutive_429_count += 1
            print(f"WARNING: Received 429 Too Many Requests. Consecutive count: {self.consecutive_429_count}/{self.max_retries_before_switch}")
            
            if self.consecutive_429_count >= self.max_retries_before_switch:
                print(f"DEBUG: Threshold reached ({self.consecutive_429_count} >= {self.max_retries_before_switch}). triggering switch...")
                self._switch_to_next_location()
        else:
            # Optional: Reset on other errors? Or only on success?
            # For now, we only reset on explicit success to be safe, 
            # or we could reset here if we think other errors imply quota isn't the issue.
            # Let's stick to resetting only on success to be strict about consecutive 429s.
            pass

    def report_success(self):
        """Report a successful request. Resets the 429 counter."""
        if self.consecutive_429_count > 0:
            self.consecutive_429_count = 0
            # print("INFO: Request successful. 429 counter reset.")

    def _switch_to_next_location(self):
        """Switch to the next available location in the list."""
        if not self.locations:
            return

        old_location = self.get_current_location()
        self.current_location_index = (self.current_location_index + 1) % len(self.locations)
        self.consecutive_429_count = 0 # Reset counter after switch
        new_location = self.get_current_location()
        
        print(f"INFO: ----------------------------------------------------------------")
        print(f"INFO: AUTO-SWITCHING LOCATION due to excessive 429s.")
        print(f"INFO: From: {old_location}  -->  To: {new_location}")
        print(f"INFO: ----------------------------------------------------------------")
