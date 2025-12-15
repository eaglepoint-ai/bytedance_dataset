calc_total ground truth

Files
- refactor_me.py: ground truth implementation
- tests/test_refactor_me.py: pytest suite that locks behavior, including catch-all exception quirks
- Dockerfile: runs tests
- requirements.txt: pytest pin

Run locally
- python -m pip install -r requirements.txt
- pytest -q

Run with Docker
- docker build -t calc-total .
- docker run --rm calc-total
