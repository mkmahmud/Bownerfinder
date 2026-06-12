from app.services.upload_parser import parse_upload


def test_parse_csv_upload_accepts_valid_rows() -> None:
    content = b"business_name,website,email\nAcme LLC,https://acme.test,hello@acme.test\n"

    result = parse_upload("leads.csv", content)

    assert result.total_rows == 1
    assert len(result.leads) == 1
    assert result.leads[0].normalized_business_name == "Acme"
    assert result.errors == []


def test_parse_csv_upload_reports_missing_business_name() -> None:
    content = b"business_name,website\n,https://missing.test\n"

    result = parse_upload("leads.csv", content)

    assert result.total_rows == 1
    assert result.leads == []
    assert result.errors[0].row_number == 2


def test_parse_csv_rejects_missing_required_column() -> None:
    content = b"name,website\nAcme,https://acme.test\n"

    try:
        parse_upload("leads.csv", content)
    except ValueError as exc:
        assert "Missing required column" in str(exc)
    else:
        raise AssertionError("Expected missing column validation error.")

