from pathlib import Path

from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_upload_creates_job_and_companies() -> None:
    client = TestClient(app)
    content = b"business_name,website,phone\nAcme LLC,https://acme.test,555-0100\n,https://bad.test,\n"

    response = client.post(
        "/api/v1/uploads",
        files={"file": ("leads.csv", content, "text/csv")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["job"]["total_rows"] == 2
    assert payload["job"]["valid_rows"] == 1
    assert payload["job"]["invalid_rows"] == 1
    assert payload["errors"][0]["row_number"] == 3

    companies_response = client.get(f"/api/v1/jobs/{payload['job']['id']}/companies")
    assert companies_response.status_code == 200
    companies = companies_response.json()
    assert companies[0]["business_name"] == "Acme LLC"
    assert companies[0]["normalized_business_name"] == "Acme"


def test_upload_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/uploads",
        files={"file": ("leads.txt", b"business_name\nAcme\n", "text/plain")},
    )

    assert response.status_code == 422


def teardown_module() -> None:
    engine.dispose()
    storage = Path(__file__).resolve().parent / ".test_storage"
    for path in sorted(storage.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
