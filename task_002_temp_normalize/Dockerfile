FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ids.py test_ids.py PLAN.md TRAJECTORY.txt ./

CMD ["pytest", "-q"]
