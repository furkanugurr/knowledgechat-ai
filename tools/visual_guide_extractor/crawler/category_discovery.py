"""Discover and classify critical guide pages under one trusted root."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup


@dataclass(frozen=True, slots=True)
class DiscoveredPage:
    title: str
    category: str
    category_key: str
    url: str


class CriticalCategoryDiscovery:
    CATEGORY_PREFIXES = {
        "guvenlik-ayarlari": ("Güvenlik Ayarları", "guvenlik_ayarlari"),
        "nat-yapilandirmasi": ("NAT Yapılandırması", "nat"),
        "ag-yapilandirmasi": ("Ağ Yapılandırması", "ag_yapilandirmasi"),
        "kullanici-yonetimi": ("Kullanıcı Yönetimi", "kullanici_yonetimi"),
        "vpn-yonetimi": ("VPN / Uzak Erişim", "vpn"),
    }

    def discover(self, html: str, guide_root: str) -> list[DiscoveredPage]:
        root = self.normalize_url(guide_root)
        root_parts = urlsplit(root)
        root_path = root_parts.path.rstrip("/") + "/"
        found: dict[str, DiscoveredPage] = {}
        for anchor in BeautifulSoup(html, "html.parser").select("a[href]"):
            title = anchor.get_text(" ", strip=True)
            if not title:
                continue
            url = self.normalize_url(urljoin(root, anchor.get("href", "")))
            parts = urlsplit(url)
            if parts.netloc != root_parts.netloc or not parts.path.startswith(root_path):
                continue
            relative = unquote(parts.path[len(root_path):]).strip("/")
            segments = relative.split("/")
            if len(segments) != 2 or segments[0].casefold() not in self.CATEGORY_PREFIXES:
                continue
            category, key = self.CATEGORY_PREFIXES[segments[0].casefold()]
            if segments[0].casefold() == "guvenlik-ayarlari" and segments[1].casefold() == "guvenlik-kurallari":
                category, key = "Güvenlik Kuralları", "guvenlik_kurallari"
            found[url.casefold()] = DiscoveredPage(title, category, key, url)
        return sorted(found.values(), key=lambda item: (item.category_key, item.title.casefold()))

    @staticmethod
    def normalize_url(url: str) -> str:
        parts = urlsplit(url.strip())
        path = "/".join(segment for segment in parts.path.split("/") if segment)
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), "/" + path + ("/" if path else ""), "", ""))
