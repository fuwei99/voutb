FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# Install dependencies
COPY requirements.txt .
RUN pip cache purge && pip install --no-cache-dir -r requirements.txt

# Install 7z for robust config decryption (unzip lacks AES/LZMA support)
RUN apt-get update && apt-get install -y p7zip-full && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app/ .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create a directory for the credentials
RUN mkdir -p /app/credentials

# Expose the port
EXPOSE 8050

# Set entrypoint to handle config decryption
ENTRYPOINT ["/app/entrypoint.sh"]

# Command to run the application
# Use the default Hugging Face port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]