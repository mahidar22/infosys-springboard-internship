from services.api_client import APIClient

def fetch_analytics(client: APIClient, filters=None): return client.get_analytics(filters)
