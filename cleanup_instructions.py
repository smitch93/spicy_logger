import re, sqlite3, pathlib

db_path = pathlib.Path("Spicy_Recipe_Logger_App/recipes.db")
db = sqlite3.connect(str(db_path))
db.row_factory = sqlite3.Row

rows = db.execute("SELECT id, instructions FROM recipes WHERE instructions IS NOT NULL").fetchall()
changed = 0
for r in rows:
    lines = []
    for raw in (r["instructions"] or "").splitlines():
        cleaned = re.sub(r'^\s*(?:\d+[.)]\s*|[-•]\s*)', '', raw).strip()
        if cleaned:
            lines.append(cleaned)
    new = "\n".join(lines)
    if new != r["instructions"]:
        db.execute("UPDATE recipes SET instructions = ? WHERE id = ?", (new, r["id"]))
        changed += 1
db.commit()
db.close()
print(f"Normalized instruction steps for {changed} recipe(s).")
