FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install quality tools
RUN pip install pylint radon pytest-benchmark

# Copy everything
COPY . .

# Default: run all tests including quality checks
CMD ["pytest", "-v", "--tb=short"]
