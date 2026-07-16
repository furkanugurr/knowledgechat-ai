"""HTTP loading and temporary image download support."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx


class PageLoader:
    """Load static guide HTML and its public images with conservative limits."""

    def __init__(self, timeout: float = 30.0, retries: int = 3, rate_limit_seconds: float = 0.5) -> None:
        self._retries = retries
        self._rate_limit_seconds = rate_limit_seconds
        self._last_request_at = 0.0
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "KnowledgeChat-VisualGuide-PoC/1.0"},
        )

    def close(self) -> None:
        """Close the managed HTTP client."""
        self._client.close()

    def __enter__(self) -> "PageLoader":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def load_page(self, url: str) -> str:
        """Return one HTML guide page."""
        response = self._get(url)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            raise ValueError(f"Guide page did not return HTML: {url}")
        try:
            return response.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Guide page is not valid UTF-8: {url}") from exc

    def download_image(self, url: str, destination: Path) -> Path:
        """Download one image using a stable, collision-resistant filename."""
        response = self._get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"Guide image did not return image data: {url}")

        suffix = Path(urlparse(url).path).suffix.lower() or ".img"
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        stem = Path(urlparse(url).path).stem or "image"
        destination.mkdir(parents=True, exist_ok=True)
        image_path = destination / f"{stem}-{digest}{suffix}"
        image_path.write_bytes(response.content)
        return image_path

    def _get(self, url: str) -> httpx.Response:
        """GET with a polite delay and bounded retry/backoff."""
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            wait = self._rate_limit_seconds - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
            try:
                response = self._client.get(url)
                self._last_request_at = time.monotonic()
                response.raise_for_status()
                return response
            except (httpx.HTTPError, OSError) as exc:
                last_error = exc
                if attempt < self._retries:
                    time.sleep(min(2 ** attempt, 8))
        raise RuntimeError(f"Request failed after retries: {url}") from last_error
