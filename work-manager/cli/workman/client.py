import os

import httpx

BASE_URL = os.getenv("WORKMAN_API_URL", "http://localhost:8000").rstrip("/")


class APIError(RuntimeError):
    pass


class WorkmanClient:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    def request(self, method: str, path: str, **kwargs):
        response = self.client.request(method, path, **kwargs)
        if response.is_success:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text
        try:
            payload = response.json()
        except Exception:
            payload = response.text
        raise APIError(f"{response.status_code}: {payload}")


client = WorkmanClient()
