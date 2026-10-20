from utils.validation import validate_lead_payload, validate_email, validate_url

def test_lead_validation_reports_required_and_bad_fields():
    errors=validate_lead_payload({"company_name":"","email":"wrong","website":"not url","company_size":"huge"})
    assert len(errors)>=3

def test_optional_valid_fields_pass():
    assert validate_email("")==[]
    assert validate_url("https://example.com")==[]
    assert validate_lead_payload({"company_name":"Acme","email":"a@b.com","website":"example.com","company_size":"51-200"})==[]
