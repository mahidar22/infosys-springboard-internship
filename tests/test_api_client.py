import httpx
from utils.config import Settings
from services.api_client import APIClient, BackendAPIError

def test_demo_client_crud_and_import():
    client=APIClient(Settings(demo_mode=True))
    before=len(client.list_leads())
    created=client.create_lead({"company_name":"Test Co","email":"test@example.com"})
    assert created["_demo"] is True
    assert len(client.list_leads())==before+1
    result=client.import_leads("x.csv",b"company_name,contact_name\nImported Co,Ada\n")
    assert result["imported"]==1

def test_non_demo_client_unwraps_data_envelope():
    transport=httpx.MockTransport(lambda req:httpx.Response(200,json={"data":[{"id":"1","company_name":"Live"}]}))
    client=APIClient(Settings(demo_mode=False,backend_base_url="https://example.test"),transport=transport)
    assert client.list_leads()==[{"id":"1","company_name":"Live"}]
