import abc
from dataclasses import dataclass
from typing import List, Optional
import urllib.request
import ssl
import time

@dataclass
class DiscoveredItem:
    source_id: str
    source_name: str
    source_page: str
    original_url: str
    thumbnail_url: str
    title: str
    category: str
    shrine: str
    license_text: str

class BaseAdapter(abc.ABC):
    def __init__(self, config: dict):
        self.config = config
        self.source_id = config.get("id", "unknown")
        self.source_name = config.get("name", "Unknown Source")
        self.license_text = config.get("license", "جميع الحقوق محفوظة للعتبة المقدسة")
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
        }

    def fetch_bytes(self, url: str, timeout: int = 25) -> bytes:
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=timeout) as resp:
            return resp.read()

    def fetch_text(self, url: str, timeout: int = 25) -> str:
        data = self.fetch_bytes(url, timeout)
        return data.decode('utf-8', errors='ignore')

    @abc.abstractmethod
    def discover_wallpapers(self, max_items: int = 100) -> List[DiscoveredItem]:
        """
        Discovers items across pages/albums up to max_items.
        """
        pass
