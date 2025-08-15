# 🌶️ Spicy Recipe Logger

**Live Demo**:(https://spicy-logger.onrender.com)

![CI](https://img.shields.io/github/actions/workflow/status/smitch93/spicy_logger/ci.yml?branch=main)
![License](https://img.shields.io/badge/license-MIT-informational)

A single-file Flask web app to **capture, browse, and filter spicy recipes** — with a modern UI, carousel view, and Markdown importing.

![List View](screenshots/list_view.png)  
![Carousel View](screenshots/carousel_view.png)  
![Edit Form](screenshots/edit_form.png)
![Dark Theme](screenshots/dark_mode.png)

---

## 🚀 Why It Matters

This project is a great portfolio piece because it demonstrates:

- **Backend CRUD**: Flask + SQLite
- **Markdown parsing → database import**
- **JSON API** endpoints
- **UI integration**: Bootstrap 5 + Swiper.js
- **Filters and sorting**
- **Deployment ready** for Render / Railway

It’s compact, but touches all the bases of full-stack development.

---

## 🛠️ Stack

- **Backend:** Flask 3, SQLite
- **Frontend:** Bootstrap 5, Swiper.js
- **Testing:** pytest
- **Deployment:** Render / Railway

---

## ✨ Features

- Add, edit, and delete recipes  
- Filters: **Cuisine**, **Vegetarian**, **Tried**  
- Toggle between **list** and **carousel** view  
- Soft de-duplication on import (no duplicate title+cuisine)  
- Markdown importer (see format below)  
- JSON API at `/api/recipes`  
- Health check at `/healthz`

---

## 📥 Import Format Example

You can paste multiple sections at once.
The importer will skip duplicates based on title + cuisine.

Paste into the **Import** page to quickly add recipes:

```markdown
### 1. Mapo Tofu (Chinese-Sichuan Style)
**Mood:** Weeknight fire

**Ingredients:**
- 1 lb tofu
- 2 tbsp doubanjiang
- 1 tsp Sichuan peppercorns, ground

**Instructions:**
1. Bloom paste and aromatics.
2. Simmer tofu in sauce.
3. Finish with scallions and peppercorn.
```
---

## 💻 Run Locally

    # Clone the repo
    git clone https://github.com/smitch93/spicy_logger.git
    cd spicy_logger

    # Create & activate a virtual environment (PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # Install dependencies
    pip install -r requirements.txt

    # Run the app (dev mode)
    $env:FLASK_DEBUG="1"
    python Spicy_Recipe_Logger_App.py
    # Open http://127.0.0.1:5000

---

## 📡 API Endpoints

**List recipes (JSON)**

    GET /api/recipes?q=&cuisine=&veg=&tried=

Returns a JSON array (max 200). Example:

    [
      {
        "id": 1,
        "title": "Mapo Tofu",
        "cuisine": "Chinese-Sichuan Style",
        "vegetarian": 0,
        "tried": 0,
        "created_at": "2025-08-14T18:32:15"
      }
    ]

**Health check**

    GET /healthz

Returns:

    { "ok": true }

---

## 🖼 Screenshots

*(Add real screenshots to `/screenshots` and update names as needed.)*

- List view: `screenshots/list-view.png`  
- Carousel view: `screenshots/carousel-view.png`  
- Edit form: `screenshots/edit-form.png`

Embed like:

    ![List view](screenshots/list-view.png)
    ![Carousel view](screenshots/carousel-view.png)
    ![Edit form](screenshots/edit-form.png)
