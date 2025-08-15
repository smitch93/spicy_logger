import json
import Spicy_Recipe_Logger_App as appmod

def test_add_and_list():
    client = appmod.app.test_client()

    resp = client.post("/add", data={
        "title":"Test Mapo", "cuisine":"Sichuan", "mood":"fiery",
        "ingredients":"tofu\nchili", "instructions":"cook\nserve",
        "spice_level":"8", "rating":"5", "tags":"tofu", "tried":"on"
    }, follow_redirects=True)
    assert resp.status_code == 200

    resp = client.get("/api/recipes")
    data = json.loads(resp.data)
    assert any(r["title"]=="Test Mapo" for r in data)
