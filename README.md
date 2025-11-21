# test-python-app

Test Python Application

## Version
1.0.0

## Requirements
- Python 3.11+

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python local_start.py
```

Or directly:
```bash
python -m uvicorn src.main.python.test_python_app.app:app --reload
```

## Stop

```bash
python local_shutdown.py
```

## API Documentation
- OpenAPI UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Health Check
- Health: http://localhost:8000/health
