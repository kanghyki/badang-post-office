#!/bin/bash

python -m venv .venv
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
