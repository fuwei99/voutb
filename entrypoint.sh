#!/bin/bash
set -e

# Define paths
CONFIG_ZIP="/app/config.zip"
CONFIG_JSON="/app/config.json"

# Check if config.zip exists
if [ -f "$CONFIG_ZIP" ]; then
    echo "Found config.zip, attempting to decrypt..."
    
    if [ -z "$CONFIG_PASSWORD" ]; then
        echo "ERROR: CONFIG_PASSWORD environment variable is not set!"
        echo "Please provide the password to decrypt config.zip"
        exit 1
    fi

    # Decrypt config.zip using 7z
    # x: extract with full paths
    # -p: password (no space)
    # -y: assume yes on all queries (overwrite)
    # -o: output directory (no space)
    
    7z x -p"$CONFIG_PASSWORD" -y "$CONFIG_ZIP" -o/app
    
    # Check if we now have a config.json in /app
    # 7z should extract it exactly as it was stored. 
    # If using pyzipper default, it usually stores relative paths.
    
    if [ -f "/app/app/config.json" ]; then
        mv /app/app/config.json /app/config.json
        rmdir /app/app
    elif [ ! -f "$CONFIG_JSON" ]; then
        echo "WARNING: Unzipped file but could not find config.json at /app/config.json"
        ls -R /app
    fi

    echo "Decryption successful."
    
    # Optional: Remove zip after decryption for cleaner env (though password is env var anyway)
    # rm "$CONFIG_ZIP"
else
    echo "Notice: config.zip not found. Assuming config.json exists or is not needed."
fi

# Run the CMD passed to docker run
exec "$@"
