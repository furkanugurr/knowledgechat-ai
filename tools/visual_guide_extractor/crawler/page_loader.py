"""HTTP loading and temporary image download support."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import httpx


class PageLoader:
    """Load static guide HTML and its public images with conservative limits."""

    def __init__(self, timeout: float = 30.0) -> None:
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
        response = self._client.get(url)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            raise ValueError(f"Guide page did not return HTML: {url}")
        try:
            return response.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Guide page is not valid UTF-8: {url}") from exc

    def download_image(self, url: str, destination: Path) -> Path:
        """Download one image using a stable, collision-resistant filename."""
        response = self._client.get(url)
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
