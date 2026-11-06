"""HTTP shell for the URL shortener.

This base is the imperative shell: it talks HTTP, maps domain results to
status codes, and gets its KeyValueStore injected by the composition root.
Serve with ``uvicorn my_namespace.urlshortener_api.app:create_app --factory``.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from my_namespace import shortener
from my_namespace.keyvaluestore import create_store
from my_namespace.keyvaluestore.interface import KeyValueStore


class ShortenRequest(BaseModel):
    url: str


def create_app(store: KeyValueStore | None = None) -> FastAPI:
    """Build the FastAPI app.

    ``store=None`` lets the keyvaluestore factory pick the backend from the
    environment ($KV_BACKEND); tests inject an InMemoryStore directly.
    """
    app = FastAPI(title="urlshortener", version="0.1.0")
    app.state.kv_store = store if store is not None else create_store()

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.post("/shorten", status_code=201)
    def shorten_url(payload: ShortenRequest, request: Request) -> dict:
        try:
            result = shortener.shorten(app.state.kv_store, payload.url)
        except shortener.InvalidUrlError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except shortener.CodeCollisionError as exc:
            # transient: ask the client to retry
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"code": result.code, "short_url": f"{request.base_url}{result.code}", "url": result.url}

    # 307 keeps method and body intact and is not permanently cached by
    # browsers, unlike 301.
    @app.get("/{code}")
    def redirect_to_url(code: str) -> RedirectResponse:
        url = shortener.resolve(app.state.kv_store, code)
        if url is None:
            raise HTTPException(status_code=404, detail=f"unknown code: {code!r}")
        return RedirectResponse(url, status_code=307)

    return app
