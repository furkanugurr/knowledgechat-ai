"""Static HTML crawling components."""

from .page_loader import PageLoader
from .parser import GuidePageParser
from .category_discovery import CriticalCategoryDiscovery, DiscoveredPage

__all__ = ["CriticalCategoryDiscovery", "DiscoveredPage", "GuidePageParser", "PageLoader"]
