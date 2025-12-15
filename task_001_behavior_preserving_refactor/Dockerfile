FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY refactor_me.py ./refactor_me.py
COPY tests ./tests

CMD ["pytest", "-q"]
