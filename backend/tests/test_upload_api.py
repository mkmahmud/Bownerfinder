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

    from app.api.v1 import uploads as uploads_module

    uploads_module.schedule_job_pipeline = lambda *args, **kwargs: None

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


def test_results_and_exports_api() -> None:
    client = TestClient(app)
    content = b"business_name,website,email\nAcme LLC,https://acme.test,hello@acme.test\n"

    from app.api.v1 import uploads as uploads_module

    uploads_module.schedule_job_pipeline = lambda *args, **kwargs: None

    upload_response = client.post(
        "/api/v1/uploads",
        files={"file": ("results.csv", content, "text/csv")},
    )
    job_id = upload_response.json()["job"]["id"]

    results_response = client.get("/api/v1/results", params={"job_id": job_id})
    assert results_response.status_code == 200
    results = results_response.json()
    assert results["total"] == 1
    assert results["items"][0]["business_name"] == "Acme LLC"

    export_response = client.post(
        "/api/v1/exports",
        json={"format": "csv", "job_id": job_id},
    )
    assert export_response.status_code == 201
    export_payload = export_response.json()
    assert export_payload["export"]["status"] == "completed"
    download_response = client.get(f"/api/v1/exports/{export_payload['export']['id']}/download")
    assert download_response.status_code == 200


def teardown_module() -> None:
    engine.dispose()
    storage = Path(__file__).resolve().parent / ".test_storage"
    for path in sorted(storage.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
