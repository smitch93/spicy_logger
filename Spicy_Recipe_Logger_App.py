import html
import re
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Dict
from flask import Flask, request, redirect, url_for, render_template_string, flash
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-only-secret")
DEBUG_MODE = os.getenv("FLASK_DEBUG", "0") == "1"



APP_TITLE = "Spicy Recipe Logger"
DB_PATH = Path(__file__).with_suffix("") / "recipes.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ----------------------- DB Utils -----------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                cuisine TEXT,
                mood TEXT,
                ingredients TEXT,
                instructions TEXT,
                spice_level INTEGER,
                rating INTEGER,
                tags TEXT,
                source TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # add vegetarian, tried if missing
        cols = {row["name"] for row in db.execute("PRAGMA table_info(recipes)")}
        if "vegetarian" not in cols:
            db.execute("ALTER TABLE recipes ADD COLUMN vegetarian INTEGER DEFAULT NULL")  # 0/1/NULL
        if "tried" not in cols:
            db.execute("ALTER TABLE recipes ADD COLUMN tried INTEGER DEFAULT NULL")
        db.commit()


# Initialize the DB at import time (Flask 3.x safe)
with app.app_context():
    init_db()


# ----------------------- Parsing -----------------------
SECTION_RE = re.compile(r"^###\s+\d+\.\s*(.+)$", re.MULTILINE)  # e.g., ### 1. Mapo Tofu
FIELD_RE = re.compile(r"^\*\*Mood:\*\*\s*(.+)$", re.MULTILINE)
ING_HEADER_RE = re.compile(r"^\*\*Ingredients:\*\*\s*$", re.MULTILINE)
INS_HEADER_RE = re.compile(r"^\*\*Instructions:\*\*\s*$", re.MULTILINE)
SEPARATOR_RE = re.compile(r"^---\s*$", re.MULTILINE)


def parse_markdown_collection(md_text: str) -> List[Dict]:
    """Parse the Spicy Recipe Collection markdown into structured dicts.
    Assumes sections separated by headers like '### n. Title' and '---'.
    """
    recipes = []
    # Find all headers with positions
    headers = [(m.group(1).strip(), m.start()) for m in SECTION_RE.finditer(md_text)]
    # Append end position
    doc_end = len(md_text)
    spans = []
    for i, (title, start) in enumerate(headers):
        end = headers[i + 1][1] if i + 1 < len(headers) else doc_end
        spans.append((title, start, end))

    for title, start, end in spans:
        chunk = md_text[start:end]
        # Mood
        mood_match = FIELD_RE.search(chunk)
        mood = mood_match.group(1).strip() if mood_match else None
        # Ingredients
        ingredients = []
        ing_header = ING_HEADER_RE.search(chunk)
        if ing_header:
            ing_start = ing_header.end()
            # Stop at Instructions header or separator or end
            stop_candidates = [
                m.start()
                for m in [
                    INS_HEADER_RE.search(chunk, ing_start),
                    SEPARATOR_RE.search(chunk, ing_start),
                ]
                if m
            ]
            ing_end = min(stop_candidates) if stop_candidates else len(chunk)
            ing_block = chunk[ing_start:ing_end].strip()
            for line in ing_block.splitlines():
                line = line.strip(" \t-•")
                if line:
                    ingredients.append(line)
        # Instructions
        instructions = []
        ins_header = INS_HEADER_RE.search(chunk)
        if ins_header:
            ins_start = ins_header.end()
            stop_candidates = [
                m.start()
                for m in [
                    SEPARATOR_RE.search(chunk, ins_start),
                    SECTION_RE.search(chunk, ins_start),
                ]
                if m
            ]
            ins_end = min(stop_candidates) if stop_candidates else len(chunk)
            ins_block = chunk[ins_start:ins_end].strip()
            for line in ins_block.splitlines():
    line = line.strip()
    if not line:
        continue
    # Strip any numbering/bullets from imported text; store plain step
    line = re.sub(r'^\s*(?:\d+[.)]\s*|[-•]\s*)', '', line)
    instructions.append(line)
        # Guess cuisine from title parenthesis e.g., (Chinese-Sichuan Style)
        cuisine = None
        m = re.search(r"\(([^)]+)\)", title)
        if m:
            cuisine = m.group(1)
            title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
        recipes.append(
            {
                "title": title,
                "cuisine": cuisine,
                "mood": mood,
                "ingredients": "\n".join(ingredients) if ingredients else None,
                "instructions": "\n".join(instructions) if instructions else None,
                "spice_level": None,
                "rating": None,
                "tags": None,
                "source": "Imported from Markdown",
            }
        )
    return recipes


# ----------------------- HTML Base -----------------------
BASE_HTML = """
<!doctype html>
<html lang="en" data-theme="spicy">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }}</title>

  <!-- Inter font -->
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- Bootstrap -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- Swiper (modern carousel) -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css"/>

  <style>
    /* ===== THEME VARIABLES ===== */
    :root{
      --bg: #f7f7fb; --card: #ffffff; --ink: #1f2330; --muted: #6c7480;
      --brand: #f2495c; --brand-2: #ff8b5e; --ring:#e7e8ef;
      --shadow: 0 8px 20px rgba(31,35,48,0.06), 0 2px 6px rgba(31,35,48,0.04);
      --radius-card: 16px; --radius-pill:999px;
    }
    /* Palettes */
    [data-theme="spicy"] { --brand:#f2495c; --brand-2:#ff8b5e; --bg:#f7f7fb; --card:#fff; --ink:#1f2330; }
    [data-theme="emerald"] { --brand:#00b37a; --brand-2:#56d364; --bg:#f4fbf8; --card:#fff; --ink:#112a22; }
    [data-theme="violet"] { --brand:#7c4dff; --brand-2:#b388ff; --bg:#f7f5ff; --card:#fff; --ink:#1f1a33; }
    [data-theme="charcoal"] { --brand:#ff6b6b; --brand-2:#ffa36c; --bg:#0f1115; --card:#161922; --ink:#e9edf5; --muted:#a9b0bf; --ring:#2a2f3b; }

    /* base */
    html,body { background: var(--bg); color: var(--ink); font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
    .container { max-width: 1120px; }

    /* glassy navbar */
    .navbar {
      position: sticky; top: 0; z-index: 100;
      background: color-mix(in oklab, var(--card) 80%, transparent) !important;
      backdrop-filter: saturate(180%) blur(12px);
      border-bottom: 1px solid var(--ring);
    }
    .btn { border-radius: 12px; }
    .btn-primary { background-image: linear-gradient(135deg, var(--brand), var(--brand-2)); border: 0; }
    .btn-outline-dark { border-color: var(--ring); color: var(--ink); }

    .form-control, .form-select { border-radius: 12px; border-color: var(--ring); }

    /* cards */
    .card {
      background: var(--card);
      border: 0;
      border-radius: var(--radius-card);
      box-shadow: var(--shadow);
      transition: transform .18s ease, box-shadow .18s ease;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(31,35,48,.09), 0 3px 10px rgba(31,35,48,.06); }
    .card-title { font-weight: 600; }
    .card-subtitle { color: var(--muted) !important; }

    /* badges + heat bar */
    .badge-spice {
      background: linear-gradient(135deg, var(--brand), var(--brand-2));
      border-radius: var(--radius-pill); padding:.35rem .6rem; color:#fff;
    }
    .badge-pill-soft { border-radius: var(--radius-pill); background: #f0f1f5; color:#3d4454; padding:.35rem .6rem; font-weight:500; }
    [data-theme="charcoal"] .badge-pill-soft { background:#232838; color:#c7cede; }
    .badge-veg { background: #e7f8f0; color:#0f7a53; }
    .badge-tried { background: #eef2ff; color:#3647d9; }
    [data-theme="charcoal"] .badge-veg { background:#163328; color:#4fd1a1; }
    [data-theme="charcoal"] .badge-tried { background:#1d2236; color:#7d8cff; }

    .heatbar { height:8px; background:#f0f1f5; border-radius:999px; overflow:hidden; }
    [data-theme="charcoal"] .heatbar { background:#232838; }
    .heatfill { height:100%; background: linear-gradient(90deg, var(--brand-2), var(--brand) 60%); width:0%; transition: width .3s ease; }

    /* Swiper tweaks */
    .swiper { padding: 4px 4px 24px; }
    .swiper-slide { width: 320px; } /* auto-like width; tweak as needed */
    .swiper-button-prev, .swiper-button-next { color: var(--ink); }
    [data-theme="charcoal"] .swiper-button-prev, [data-theme="charcoal"] .swiper-button-next { color: #e9edf5; }
    .swiper-pagination-bullet { background: var(--muted); opacity:.5; }
    .swiper-pagination-bullet-active { background: var(--brand); opacity:1; }

    /* motion safety */
    @media (prefers-reduced-motion: reduce) {
      * { transition:none!important; animation:none!important; scroll-behavior:auto!important; }
    }
  </style>
</head>
<body>
<nav class="navbar navbar-expand-lg">
  <div class="container">
    <a class="navbar-brand fw-semibold" href="{{ url_for('index') }}">🌶️ Spicy Logger</a>
    <div class="d-flex gap-2">
      <!-- Theme switcher -->
      <div class="dropdown">
        <button class="btn btn-outline-dark dropdown-toggle" data-bs-toggle="dropdown">Theme</button>
        <div class="dropdown-menu dropdown-menu-end">
          <button class="dropdown-item" onclick="setTheme('spicy')">Spicy</button>
          <button class="dropdown-item" onclick="setTheme('emerald')">Emerald</button>
          <button class="dropdown-item" onclick="setTheme('violet')">Violet</button>
          <div class="dropdown-divider"></div>
          <button class="dropdown-item" onclick="setTheme('charcoal')">Charcoal (dark)</button>
        </div>
      </div>
      <a class="btn btn-outline-dark" href="{{ url_for('import_page') }}">Import</a>
      <a class="btn btn-primary" href="{{ url_for('add_recipe') }}">Add Recipe</a>
    </div>
  </div>
</nav>

<div class="container mt-4">
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div>
        {% for m in messages %}<div class="alert alert-info border-0 shadow-sm">{{ m }}</div>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {{ body|safe }}
</div>

<!-- Bootstrap + Swiper JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
<script>
  // Theme persistence
  function setTheme(name){
    document.documentElement.setAttribute('data-theme', name);
    localStorage.setItem('sr_theme', name);
  }
  (function(){
    const saved = localStorage.getItem('sr_theme');
    if (saved) document.documentElement.setAttribute('data-theme', saved);
  })();

  // init Swiper if present
  function initRecipeSwiper(){
    const el = document.querySelector('.recipe-swiper');
    if(!el) return;
    new Swiper(el, {
      slidesPerView: 'auto',
      spaceBetween: 16,
      freeMode: false,
      loop: false,
      grabCursor: true,
      keyboard: { enabled: true },
      mousewheel: { forceToAxis: true, sensitivity: 0.5 },
      navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
      pagination: { el: '.swiper-pagination', clickable: true },
      breakpoints: {
        0: { spaceBetween: 12 },
        576: { spaceBetween: 14 },
        992: { spaceBetween: 16 }
      }
    });
  }
  document.addEventListener('DOMContentLoaded', initRecipeSwiper);
</script>
</body>
</html>
"""



def render(page_title: str, body_html: str):
    return render_template_string(
        BASE_HTML, title=f"{APP_TITLE} – {page_title}", body=body_html
    )


# ----------------------- Routes -----------------------

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "created_at_desc")
    flt_cuisine = request.args.get("cuisine", "").strip()
    flt_veg = request.args.get("veg", "")      # '', '1', '0'
    flt_tried = request.args.get("tried", "")  # '', '1', '0'
    view_mode = request.args.get("view", "list")  # 'list' or 'carousel'

    order_by = {
        "created_at_desc": "created_at DESC",
        "title": "title COLLATE NOCASE ASC",
        "cuisine": "cuisine COLLATE NOCASE ASC",
    }.get(sort, "created_at DESC")

    sql = "SELECT * FROM recipes"
    params = []
    wheres = []

    if q:
        wheres.append("(title LIKE ? OR cuisine LIKE ? OR tags LIKE ? OR mood LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like, like])
    if flt_cuisine:
        wheres.append("cuisine = ?")
        params.append(flt_cuisine)
    if flt_veg in ("0", "1"):
        wheres.append("IFNULL(vegetarian, 0) = ?")
        params.append(int(flt_veg))
    if flt_tried in ("0", "1"):
        wheres.append("IFNULL(tried, 0) = ?")
        params.append(int(flt_tried))

    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += f" ORDER BY {order_by}"

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
        cuisines = [
            row[0]
            for row in db.execute(
                "SELECT DISTINCT cuisine FROM recipes "
                "WHERE cuisine IS NOT NULL AND TRIM(cuisine) <> '' "
                "ORDER BY cuisine COLLATE NOCASE"
            ).fetchall()
        ]

    # --- Build cards for BOTH views ---
    grid_cards = []
    carousel_slides = []

    for r in rows:
        safe_title = html.escape(r["title"] or "")
        safe_cuisine = html.escape(r["cuisine"] or "")
        safe_mood = html.escape(r["mood"] or "")
        veg_badge = "<span class='badge badge-pill-soft badge-veg me-1'>Vegetarian</span>" if r["vegetarian"] else ""
        tried_badge = "<span class='badge badge-pill-soft badge-tried me-1'>Tried</span>" if r["tried"] else ""
        heat_pct = f"{max(0, min(10, int(r['spice_level']))) * 10}%" if r["spice_level"] is not None else None

        card_inner = f"""
          <div class='card-body'>
            <div class='d-flex justify-content-between align-items-start'>
              <div>
                <h5 class='card-title mb-1'>{safe_title}</h5>
                <div class='card-subtitle mb-2'>{safe_cuisine}</div>
              </div>
              <span class='badge badge-spice'>🌶️</span>
            </div>
            <p class='mb-2 text-body'>{safe_mood}</p>
            <div class='mb-2'>{veg_badge}{tried_badge}</div>
            {"<div class='heatbar mb-3'><div class='heatfill' style='width:" + heat_pct + ";'></div></div>" if heat_pct else ""}
            <div class='d-flex gap-2'>
              <a href='{url_for('view_recipe', recipe_id=r["id"])}' class='btn btn-sm btn-outline-dark'>View</a>
              <form method="post" action="{url_for('delete_recipe', recipe_id=r['id'])}" class="d-inline"
                    onsubmit="return confirm('Delete {safe_title}?');">
                <button class="btn btn-sm btn-danger">Delete</button>
              </form>
            </div>
          </div>
        """

        grid_cards.append(
            f"<div class='col'><div class='card shadow-sm h-100'>{card_inner}</div></div>"
        )
        carousel_slides.append(
            f"<div class='swiper-slide'><div class='card shadow-sm'>{card_inner}</div></div>"
        )

    # --- Build filters UI pieces ---
    cuisine_options = "".join(
        f"<option value='{html.escape(c)}' {'selected' if c == flt_cuisine else ''}>{html.escape(c)}</option>"
        for c in cuisines
    )
    veg_options = f"""
    <option value='' {'selected' if flt_veg == '' else ''}>Any</option>
    <option value='1' {'selected' if flt_veg == '1' else ''}>Vegetarian</option>
    <option value='0' {'selected' if flt_veg == '0' else ''}>Not vegetarian</option>
    """
    tried_options = f"""
    <option value='' {'selected' if flt_tried == '' else ''}>Any</option>
    <option value='1' {'selected' if flt_tried == '1' else ''}>Tried</option>
    <option value='0' {'selected' if flt_tried == '0' else ''}>Not tried</option>
    """

    # Preserve current params when toggling view
    params_keep = request.args.to_dict(flat=True)
    params_keep["view"] = "carousel" if view_mode != "carousel" else "list"
    toggle_label = "Switch to Carousel" if view_mode != "carousel" else "Switch to List"
    toggle_url = url_for("index", **params_keep)

    # --- Compose form ---
    top_form = f"""
    <div class="shadow-sm p-3 rounded-4 bg-white mb-3">
      <form class='row g-2' method='get'>
        <div class='col-md-4'>
          <input name='q' value='{html.escape(q)}' class='form-control' placeholder='Search by title, cuisine, tags, mood'>
        </div>
        <div class='col-md-3'>
          <select name='cuisine' class='form-select'>
            <option value='' {'selected' if not flt_cuisine else ''}>All cuisines</option>
            {cuisine_options}
          </select>
        </div>
        <div class='col-md-2'>
          <select name='veg' class='form-select'>
            {veg_options}
          </select>
        </div>
        <div class='col-md-2'>
          <select name='tried' class='form-select'>
            {tried_options}
          </select>
        </div>
        <div class='col-md-1'>
          <button class='btn btn-primary w-100'>Go</button>
        </div>
        <div class='col-12 mt-2 d-flex flex-wrap gap-2 align-items-center'>
          <select name='sort' class='form-select w-auto'>
            <option value='created_at_desc' {'selected' if sort == 'created_at_desc' else ''}>Newest</option>
            <option value='title' {'selected' if sort == 'title' else ''}>Title</option>
            <option value='cuisine' {'selected' if sort == 'cuisine' else ''}>Cuisine</option>
          </select>
          <a class='btn btn-outline-dark' href='{url_for('index')}'>Reset</a>
          <a class='btn btn-outline-dark' href='{toggle_url}'>{toggle_label}</a>
        </div>
      </form>
    </div>
    """

    # --- Choose layout ONCE (no duplicates) ---
    if view_mode == "carousel":
        list_html = f"""
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h5 class='m-0'>Recipes</h5>
          <div class='d-flex gap-2'>
            <button type="button" class="btn btn-outline-dark btn-sm swiper-button-prev">◀</button>
            <button type="button" class="btn btn-outline-dark btn-sm swiper-button-next">▶</button>
          </div>
        </div>
        <div class="recipe-swiper swiper">
          <div class="swiper-wrapper">
            {''.join(carousel_slides) or '<p class="text-muted">No recipes yet. Import or add one!</p>'}
          </div>
          <div class="swiper-pagination"></div>
        </div>
        """
    else:
        list_html = f"""
        <div class='row row-cols-1 row-cols-md-2 row-cols-lg-3 g-3'>
          {''.join(grid_cards) or '<p>No recipes yet. Import or add one!</p>'}
        </div>
        """

    body = top_form + list_html
    return render("Home", body)




@app.route("/recipe/<int:recipe_id>")
def view_recipe(recipe_id: int):
    with get_db() as db:
        r = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if not r:
        flash("Recipe not found")
        return redirect(url_for('index'))

    ing_html = "".join(f"<li>{html.escape(line)}</li>" for line in (r["ingredients"] or "").splitlines())
    ins_html = "".join(f"<li>{html.escape(line)}</li>" for line in (r["instructions"] or "").splitlines())

    # badges
    badges = []
    if r["vegetarian"]:
        badges.append("<span class='badge bg-success me-1'>Vegetarian</span>")
    if r["tried"]:
        badges.append("<span class='badge bg-secondary me-1'>Tried</span>")
    badges_html = "".join(badges)

    body = f"""
      <div class='mb-3 d-flex gap-2'>
        <a class='btn btn-sm btn-outline-secondary' href='{url_for('index')}'>← Back</a>
        <a class='btn btn-sm btn-primary' href='{url_for('edit_recipe', recipe_id=recipe_id)}'>Edit</a>
        <form method="post" action="{url_for('delete_recipe', recipe_id=recipe_id)}" onsubmit="return confirm('Delete this recipe? This cannot be undone.');">
          <button class="btn btn-sm btn-danger">Delete</button>
        </form>
      </div>
      <div class='card shadow-sm'>
        <div class='card-body'>
          <h3 class='card-title'>{html.escape(r['title'])}</h3>
          <h6 class='text-muted'>{html.escape(r['cuisine'] or '')}</h6>
          <p class='mt-2'><b>Mood:</b> {html.escape(r['mood'] or '')}</p>
          <p>{badges_html}</p>
          <div class='row'>
            <div class='col-md-6'>
              <h5>Ingredients</h5>
              <ul>{ing_html or '<em>None</em>'}</ul>
            </div>
            <div class='col-md-6'>
              <h5>Instructions</h5>
              <ol>{ins_html or '<em>None</em>'}</ol>
            </div>
          </div>
        </div>
      </div>
    """
    return render(r["title"], body)


@app.route("/add", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        data = {
            "title": request.form.get("title", "").strip(),
            "cuisine": request.form.get("cuisine", "").strip() or None,
            "mood": request.form.get("mood", "").strip() or None,
            "ingredients": request.form.get("ingredients", "").strip() or None,
            "instructions": request.form.get("instructions", "").strip() or None,
            "spice_level": int(request.form.get("spice_level")) if request.form.get("spice_level") else None,
            "rating": int(request.form.get("rating")) if request.form.get("rating") else None,
            "tags": request.form.get("tags", "").strip() or None,
            "source": "Manual",
            "created_at": datetime.now(UTC).isoformat(),
            # checkboxes: present when checked
            "vegetarian": 1 if request.form.get("vegetarian") == "on" else 0,
            "tried": 1 if request.form.get("tried") == "on" else 0,
        }
        if not data["title"]:
            flash("Title is required")
        else:
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO recipes(title,cuisine,mood,ingredients,instructions,spice_level,rating,tags,source,created_at,vegetarian,tried)
                    VALUES(:title,:cuisine,:mood,:ingredients,:instructions,:spice_level,:rating,:tags,:source,:created_at,:vegetarian,:tried)
                    """,
                    data,
                )
                db.commit()
            flash("Recipe added!")
            return redirect(url_for("index"))

    body = """
      <form method='post' class='row g-3'>
        <div class='col-md-8'>
          <label class='form-label'>Title</label>
          <input name='title' class='form-control' required>
        </div>
        <div class='col-md-4'>
          <label class='form-label'>Cuisine</label>
          <input name='cuisine' class='form-control'>
        </div>
        <div class='col-12'>
          <label class='form-label'>Mood</label>
          <input name='mood' class='form-control'>
        </div>
        <div class='col-md-6'>
          <label class='form-label'>Ingredients (one per line)</label>
          <textarea name='ingredients' rows='10' class='form-control'></textarea>
        </div>
        <div class='col-md-6'>
          <label class='form-label'>Instructions (one step per line)</label>
          <textarea name='instructions' rows='10' class='form-control'></textarea>
        </div>
        <div class='col-md-3'>
          <label class='form-label'>Spice Level (1-10)</label>
          <input name='spice_level' type='number' min='1' max='10' class='form-control'>
        </div>
        <div class='col-md-3'>
          <label class='form-label'>Rating (1-5)</label>
          <input name='rating' type='number' min='1' max='5' class='form-control'>
        </div>
        <div class='col-md-6'>
          <label class='form-label'>Tags (comma-separated)</label>
          <input name='tags' class='form-control' placeholder='tofu, weeknight, grill'>
        </div>
        <div class='col-md-3'>
          <div class="form-check mt-4">
            <input class="form-check-input" type="checkbox" name="vegetarian" id="vegAdd">
            <label class="form-check-label" for="vegAdd">Vegetarian</label>
          </div>
        </div>
        <div class='col-md-3'>
          <div class="form-check mt-4">
            <input class="form-check-input" type="checkbox" name="tried" id="triedAdd">
            <label class="form-check-label" for="triedAdd">Tried</label>
          </div>
        </div>
        <div class='col-12'>
          <button class='btn btn-primary'>Save</button>
        </div>
      </form>
    """
    return render("Add Recipe", body)


@app.route("/edit/<int:recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id: int):
    with get_db() as db:
        r = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if not r:
        flash("Recipe not found")
        return redirect(url_for('index'))

    if request.method == "POST":
        data = {
            "title": request.form.get("title", "").strip(),
            "cuisine": request.form.get("cuisine", "").strip() or None,
            "mood": request.form.get("mood", "").strip() or None,
            "ingredients": request.form.get("ingredients", "").strip() or None,
            "instructions": request.form.get("instructions", "").strip() or None,
            "spice_level": int(request.form.get("spice_level")) if request.form.get("spice_level") else None,
            "rating": int(request.form.get("rating")) if request.form.get("rating") else None,
            "tags": request.form.get("tags", "").strip() or None,
            "vegetarian": 1 if request.form.get("vegetarian") == "on" else 0,
            "tried": 1 if request.form.get("tried") == "on" else 0,
            "id": recipe_id,
        }
        with get_db() as db:
            db.execute(
                """
                UPDATE recipes
                   SET title=:title,
                       cuisine=:cuisine,
                       mood=:mood,
                       ingredients=:ingredients,
                       instructions=:instructions,
                       spice_level=:spice_level,
                       rating=:rating,
                       tags=:tags,
                       vegetarian=:vegetarian,
                       tried=:tried
                 WHERE id=:id
                """,
                data,
            )
            db.commit()
        flash("Recipe updated!")
        return redirect(url_for('view_recipe', recipe_id=recipe_id))

    veg_checked = "checked" if r["vegetarian"] else ""
    tried_checked = "checked" if r["tried"] else ""

    body = f"""
      <form method='post' class='row g-3'>
        <div class='col-md-8'>
          <label class='form-label'>Title</label>
          <input name='title' class='form-control' value='{html.escape(r['title'] or "")}' required>
        </div>
        <div class='col-md-4'>
          <label class='form-label'>Cuisine</label>
          <input name='cuisine' class='form-control' value='{html.escape(r['cuisine'] or "")}'>
        </div>
        <div class='col-12'>
          <label class='form-label'>Mood</label>
          <input name='mood' class='form-control' value='{html.escape(r['mood'] or "")}'>
        </div>
        <div class='col-md-6'>
          <label class='form-label'>Ingredients (one per line)</label>
          <textarea name='ingredients' rows='10' class='form-control'>{html.escape(r['ingredients'] or "")}</textarea>
        </div>
        <div class='col-md-6'>
          <label class='form-label'>Instructions (one step per line)</label>
          <textarea name='instructions' rows='10' class='form-control'>{html.escape(r['instructions'] or "")}</textarea>
        </div>
        <div class='col-md-3'>
          <label class='form-label'>Spice Level (1-10)</label>
          <input name='spice_level' type='number' min='1' max='10' class='form-control' value='{r['spice_level'] or ""}'>
        </div>
        <div class='col-md-3'>
          <label class='form-label'>Rating (1-5)</label>
          <input name='rating' type='number' min='1' max='5' class='form-control' value='{r['rating'] or ""}'>
        </div>
        <div class='col-md-6'>
          <label class='form-label'>Tags (comma-separated)</label>
          <input name='tags' class='form-control' value='{html.escape(r['tags'] or "")}'>
        </div>
        <div class='col-md-3'>
          <div class="form-check mt-4">
            <input class="form-check-input" type="checkbox" name="vegetarian" id="vegEdit" {veg_checked}>
            <label class="form-check-label" for="vegEdit">Vegetarian</label>
          </div>
        </div>
        <div class='col-md-3'>
          <div class="form-check mt-4">
            <input class="form-check-input" type="checkbox" name="tried" id="triedEdit" {tried_checked}>
            <label class="form-check-label" for="triedEdit">Tried</label>
          </div>
        </div>
        <div class='col-12'>
          <button class='btn btn-primary'>Save</button>
        </div>
      </form>
    """
    return render("Edit Recipe", body)


@app.route("/import", methods=["GET", "POST"])
def import_page():
    if request.method == "POST":
        md_text = request.form.get("md_text", "").strip()
        if not md_text:
            flash("Paste your markdown or text to import.")
            return redirect(url_for("import_page"))

        imported = parse_markdown_collection(md_text)
        count = 0
        with get_db() as db:
            for rec in imported:
                title = (rec.get("title") or "").strip()
                cuisine = (rec.get("cuisine") or "").strip()
                if not title:
                    continue
                exists = db.execute(
                    "SELECT id FROM recipes WHERE title = ? AND IFNULL(cuisine,'') = ? LIMIT 1",
                    (title, cuisine)
                ).fetchone()
                if exists:
                    continue
                rec.setdefault("vegetarian", None)
                rec.setdefault("tried", 0)
                rec["created_at"] = datetime.now(UTC).isoformat()
                db.execute(
                    """
                    INSERT INTO recipes(title, cuisine, mood, ingredients, instructions, spice_level, rating, tags,
                                        source, created_at, vegetarian, tried)
                    VALUES (:title, :cuisine, :mood, :ingredients, :instructions, :spice_level, :rating, :tags, :source,
                            :created_at, :vegetarian, :tried)
                    """,
                    rec,
                )
                count += 1
            db.commit()

        flash(f"Imported {count} recipe(s).")
        return redirect(url_for("index"))

    placeholder = (
        "Paste the contents of your 'Spicy Recipe Collection' document here.\n"
        "This importer expects sections like:\n\n"
        "### 1. Mapo Tofu (Chinese-Sichuan Style)\n"
        "**Mood:** …\n\n"
        "**Ingredients:**\n- item 1\n- item 2\n\n"
        "**Instructions:**\n1. step\n2. step\n\n---\n"
    )
    body = f"""
      <div class='row'>
        <div class='col-lg-10'>
          <form method='post'>
            <label class='form-label'>Paste Markdown/Text</label>
            <textarea name='md_text' rows='18' class='form-control' placeholder='{placeholder}'></textarea>
            <div class='form-text'>Pro tip: You can import multiple sections at once.</div>
            <button class='btn btn-success mt-3'>Import</button>
          </form>
        </div>
      </div>
    """
    return render("Import", body)


@app.route("/delete/<int:recipe_id>", methods=["POST"])
def delete_recipe(recipe_id: int):
    # make sure it exists (optional but nicer UX)
    with get_db() as db:
        row = db.execute("SELECT id, title FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
        if not row:
            flash("Recipe not found (maybe you already deleted it).")
            return redirect(url_for("index"))
        db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        db.commit()
    flash("Recipe deleted.")
    return redirect(url_for("index"))


from flask import jsonify

@app.errorhandler(404)
def not_found(_):
    return render("Not Found", "<div class='text-center py-5'><h3>Not found.</h3><p>Try the search box.</p></div>"), 404

@app.route("/healthz")
def healthz():
    return jsonify(ok=True), 200

@app.route("/api/recipes")
def api_recipes():
    q = request.args.get("q", "").strip()
    flt_cuisine = request.args.get("cuisine", "").strip()
    flt_veg = request.args.get("veg", "")
    flt_tried = request.args.get("tried", "")

    sql = "SELECT id,title,cuisine,mood,spice_level,rating,tags,vegetarian,tried,created_at FROM recipes"
    params, wheres = [], []
    if q:
        wheres.append("(title LIKE ? OR cuisine LIKE ? OR tags LIKE ? OR mood LIKE ?)")
        like = f"%{q}%"; params.extend([like, like, like, like])
    if flt_cuisine:
        wheres.append("cuisine = ?"); params.append(flt_cuisine)
    if flt_veg in ("0","1"):
        wheres.append("IFNULL(vegetarian,0) = ?"); params.append(int(flt_veg))
    if flt_tried in ("0","1"):
        wheres.append("IFNULL(tried,0) = ?"); params.append(int(flt_tried))
    if wheres: sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY created_at DESC LIMIT 200"

    with get_db() as db:
        rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True)
