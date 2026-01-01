FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Default entrypoint runs the meta-test benchmark reporter
CMD ["python", "evaluation/evaluations.py", "--tests", "tests/test_sequence_generator_meta.py"]
