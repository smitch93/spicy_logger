# Spicy Recipe Logger 🌶️

![CI](https://img.shields.io/github/actions/workflow/status/smitch93/spicy_logger/ci.yml?branch=main)
![License](https://img.shields.io/badge/license-MIT-informational)

Single-file Flask app to capture, browse, and filter spicy recipes.

**Live demo:** (https://spicy-logger.onrender.com)

## Why it matters
- Shows backend CRUD (Flask + SQLite), parsing (Markdown → DB), and a simple JSON API.
- Demonstrates UI integration (Bootstrap + Swiper), filters, and deployment.

## Stack
- Flask 3, SQLite
- Bootstrap 5, Swiper.js
- pytest, GitHub Actions (CI)

## Features
- CRUD (add / edit / delete)
- Filters: cuisine / vegetarian / tried
- List ↔ Carousel (Swiper) view
- Markdown importer with soft de-duplication
- JSON API: `/api/recipes`
- Health check: `/healthz`

## Run locally
```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_DEBUG="1"
python Spicy_Recipe_Logger_App.py
# open http://127.0.0.1:5000
