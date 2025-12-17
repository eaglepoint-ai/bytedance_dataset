FROM python:3.11-slim

# Install bash for compare script
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Default command - runs meta-tests
CMD ["pytest", "-v", "tests/meta_test_lru_cache.py"]
