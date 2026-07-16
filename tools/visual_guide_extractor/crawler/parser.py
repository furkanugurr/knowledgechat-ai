"""Order-preserving parser for static visual guide pages."""

from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from tools.visual_guide_extractor.schemas.extraction import (
    ContentBlock,
    GuidePage,
)


class GuidePageParser:
    """Extract useful content blocks while excluding navigation and chrome."""

    _CONTENT_SELECTORS = ("main", "article", ".content", ".markdown-body", ".container")

    def parse(self, html: str, source_url: str) -> GuidePage:
        """Parse title, text blocks, lists, and images in DOM order."""
        soup = BeautifulSoup(html, "html.parser")
        root = self._find_content_root(soup)
        title_tag = root.find("h1") or soup.find("h1") or soup.find("title")
        if title_tag is None:
            raise ValueError("Guide page has no title")

        title = title_tag.get_text(" ", strip=True)
        blocks: list[ContentBlock] = []
        image_index = 0
        for element in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol"]):
            if not isinstance(element, Tag) or self._is_nested_content(element):
                continue

            if element.name == "p" and element.find("img"):
                for child in element.children:
                    if isinstance(child, Tag) and child.name == "img":
                        image_url = self._image_url(child, source_url)
                        if image_url:
                            blocks.append(
                                ContentBlock(
                                    kind="image",
                                    image_url=image_url,
                                    image_index=image_index,
                                    alt_text=child.get("alt", "").strip(),
                                )
                            )
                            image_index += 1
                    elif isinstance(child, str) and child.strip():
                        blocks.append(ContentBlock(kind="paragraph", text=child.strip()))
                continue

            if element.name in {"ul", "ol"}:
                items = [
                    item.get_text(" ", strip=True)
                    for item in element.find_all("li", recursive=False)
                    if item.get_text(" ", strip=True)
                ]
                if items:
                    blocks.append(
                        ContentBlock(
                            kind="ordered_list" if element.name == "ol" else "unordered_list",
                            items=items,
                        )
                    )
                continue

            text = element.get_text(" ", strip=True)
            if not text:
                continue
            if element.name and element.name.startswith("h"):
                blocks.append(
                    ContentBlock(kind="heading", text=text, level=int(element.name[1]))
                )
            elif element.name == "p":
                blocks.append(ContentBlock(kind="paragraph", text=text))

        return GuidePage(page_title=title, source_url=source_url, blocks=blocks)

    @classmethod
    def _find_content_root(cls, soup: BeautifulSoup) -> Tag:
        for selector in cls._CONTENT_SELECTORS:
            candidate = soup.select_one(selector)
            if isinstance(candidate, Tag) and candidate.find("h1"):
                return candidate
        if soup.body is None:
            raise ValueError("Guide page has no body")
        return soup.body

    @staticmethod
    def _is_nested_content(element: Tag) -> bool:
        return any(parent.name in {"ul", "ol"} for parent in element.parents)

    @staticmethod
    def _image_url(image: Tag, source_url: str) -> str | None:
        source = image.get("src")
        if not isinstance(source, str) or not source.strip():
            return None
        return urljoin(source_url, source.strip())
