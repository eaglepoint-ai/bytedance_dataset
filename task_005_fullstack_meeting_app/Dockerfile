FROM python:3.11-slim
WORKDIR /app

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-anyio \
    httpx \
    sqlalchemy \
    psycopg2-binary

COPY . /app

CMD ["pytest", "tests/", "-v"]
