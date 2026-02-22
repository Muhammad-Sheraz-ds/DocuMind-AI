FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build React frontend
RUN cd frontend && npm install && npm run build

# Create data directories
RUN mkdir -p data/uploads data/chroma_db

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Start FastAPI and serve frontend from static files
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
