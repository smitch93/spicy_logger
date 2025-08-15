# 🌶️ Spicy Recipe Logger

**Live Demo**:(https://spicy-logger.onrender.com)

![CI](https://img.shields.io/github/actions/workflow/status/smitch93/spicy_logger/ci.yml?branch=main)
![License](https://img.shields.io/badge/license-MIT-informational)

A single-file Flask web app to **capture, browse, and filter spicy recipes** — with a modern UI, carousel view, and Markdown importing.

![List View](screenshots/list_view.png)  
![Carousel View](screenshots/carousel_view.png)  

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

---
