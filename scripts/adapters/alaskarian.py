from typing import List
import json
import time
from .base import BaseAdapter, DiscoveredItem

class AlAskarianAdapter(BaseAdapter):
    """
    Adapter for alaskarian.iq gallery.
    Uses JSON API endpoint: /gallery/load-more?offset={offset}
    """

    def discover_wallpapers(self, max_items: int = 100) -> List[DiscoveredItem]:
        results: List[DiscoveredItem] = []
        api_url = self.config.get("api_url", "https://alaskarian.iq/gallery/load-more")
        category = self.config.get("default_category", "العتبة العسكرية المقدسة")
        shrine = self.config.get("shrine", "مرقد الإمامين العسكريين (ع) - سامراء المشرفة")

        offset = 0
        step = 16
        consecutive_empty = 0

        print(f"[AlAskarianAdapter] Starting discovery from {api_url}...")

        while len(results) < max_items and consecutive_empty < 3:
            page_url = f"{api_url}?offset={offset}"
            try:
                raw = self.fetch_bytes(page_url)
                data = json.loads(raw.decode('utf-8'))
                items = data.get("gallery", [])
                time.sleep(0.4)
            except Exception as e:
                print(f"[AlAskarianAdapter] Error at offset {offset}: {e}")
                consecutive_empty += 1
                offset += step
                continue

            if not items:
                consecutive_empty += 1
                offset += step
                continue

            consecutive_empty = 0
            for idx, entry in enumerate(items):
                if len(results) >= max_items:
                    break
                img_url = entry.get("image")
                if not img_url:
                    continue

                # Clean escaped slashes if any
                img_url = img_url.replace("\\/", "/")

                # Extract filename as base title
                filename = img_url.split('/')[-1].split('.')[0]
                title = f"العتبة العسكرية المقدسة - لقطة {offset + idx + 1}"

                item = DiscoveredItem(
                    source_id=self.source_id,
                    source_name=self.source_name,
                    source_page="https://alaskarian.iq/gallery",
                    original_url=img_url,
                    thumbnail_url=img_url,  # Direct WebP is already fast
                    title=title,
                    category=category,
                    shrine=shrine,
                    license_text=self.license_text
                )
                results.append(item)

            offset += step

        print(f"[AlAskarianAdapter] Total items discovered: {len(results)}")
        return results
