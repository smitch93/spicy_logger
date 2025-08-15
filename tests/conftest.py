import pytest, gc, time
from pathlib import Path
import Spicy_Recipe_Logger_App as appmod

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    # point app at an isolated DB file per test
    db_path = tmp_path / "recipes.db"
    monkeypatch.setattr(appmod, "DB_PATH", db_path)

    # init schema
    with appmod.app.app_context():
        appmod.init_db()

    yield  # run the test

    # teardown: force GC so sqlite closes handles, then let tmp_path cleanup
    gc.collect()
    time.sleep(0.05)
