FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app/repository_before

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["test-score"]
