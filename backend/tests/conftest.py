import os
import sys
from pathlib import Path

TEST_STORAGE = Path(__file__).resolve().parent / ".test_storage"
TEST_STORAGE.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_STORAGE / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(TEST_STORAGE / "uploads")
os.environ["RESULT_DIR"] = str(TEST_STORAGE / "results")
os.environ["EXPORT_DIR"] = str(TEST_STORAGE / "exports")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

