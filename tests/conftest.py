import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

CORE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CORE_ROOT))
os.chdir(CORE_ROOT)
os.environ.setdefault("CORE_DB_PATH", "")


@pytest.fixture()
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    os.environ["CORE_DB_PATH"] = db_path
    from core.database import init_db

    init_db()
    yield db_path
    Path(db_path).unlink(missing_ok=True)
