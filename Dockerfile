FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories with proper permissions
RUN mkdir -p data/uploads data/chroma_db && chmod -R 777 data

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
