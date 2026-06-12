from app.services.normalization import normalize_company_name


def test_normalize_company_name_removes_common_suffixes() -> None:
    assert normalize_company_name("Acme Services LLC") == "Acme Services"
    assert normalize_company_name("Northwind GmbH") == "Northwind"
    assert normalize_company_name("Example Corp.") == "Example"

