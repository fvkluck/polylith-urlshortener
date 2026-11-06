"""API (shell) tests: full shorten→resolve round trip over HTTP.

The store is injected, so no redis and no env vars are involved.
"""

import pytest
from fastapi.testclient import TestClient

from my_namespace import shortener
from my_namespace.keyvaluestore.memory import InMemoryStore
from my_namespace.urlshortener_api import create_app


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def client(store: InMemoryStore) -> TestClient:
    return TestClient(create_app(store=store))


def test_shorten_returns_code_and_short_url(client: TestClient) -> None:
    response = client.post("/shorten", json={"url": "https://example.com/page"})
    assert response.status_code == 201
    body = response.json()
    assert body["url"] == "https://example.com/page"
    assert body["short_url"] == f"http://testserver/{body['code']}"


def test_shorten_result_resolves_via_redirect(client: TestClient, store: InMemoryStore) -> None:
    body = client.post("/shorten", json={"url": "https://example.com"}).json()
    response = client.get(f"/{body['code']}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com"
    # the shell must have gone through the core, not written the store itself
    assert shortener.resolve(store, body["code"]) == "https://example.com"


def test_unknown_code_is_404(client: TestClient) -> None:
    response = client.get("/AAAAAAA", follow_redirects=False)
    assert response.status_code == 404


def test_invalid_url_is_422(client: TestClient, store: InMemoryStore) -> None:
    response = client.post("/shorten", json={"url": "ftp://example.com"})
    assert response.status_code == 422
    assert "scheme" in response.json()["detail"]
    assert store._data == {}


def test_repeated_shorten_yields_distinct_codes(client: TestClient) -> None:
    first = client.post("/shorten", json={"url": "https://example.com"}).json()
    second = client.post("/shorten", json={"url": "https://example.com"}).json()
    assert first["code"] != second["code"]


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


def test_factory_without_store_uses_kv_backend_default(monkeypatch) -> None:
    # no store injected and no KV_BACKEND set: must default to in-memory
    monkeypatch.delenv("KV_BACKEND", raising=False)
    app = create_app()
    assert isinstance(app.state.kv_store, InMemoryStore)
