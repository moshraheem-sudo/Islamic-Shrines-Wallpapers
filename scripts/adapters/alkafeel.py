from typing import List
import urllib.request
import ssl
import json
import time
from .base import BaseAdapter, DiscoveredItem

class AlKafeelAdapter(BaseAdapter):
    """
    Adapter for pic.alkafeel.net (شبكة الكفيل العالمية - العتبة العباسية المقدسة).
    Uses REST API: https://main.pictures.alkafeel.net/api/photos/ar?filter[category_id]={id}&page={page}
    """

    def discover_wallpapers(self, max_items: int = 100) -> List[DiscoveredItem]:
        results: List[DiscoveredItem] = []
        sections = self.config.get("sections", [])
        base_api = self.config.get("api_url", "https://main.pictures.alkafeel.net/api/photos/ar")

        items_per_section = max(20, max_items // len(sections)) if sections else max_items

        for sec in sections:
            sec_id = sec.get("id")
            sec_name = sec.get("name", "شبكة الكفيل")
            sec_cat = sec.get("category", "العتبة العباسية المقدسة")
            sec_shrine = sec.get("shrine", sec_name)

            print(f"[AlKafeelAdapter] Fetching category {sec_name} (ID: {sec_id})...")
            sec_added = 0
            page = 1

            while sec_added < items_per_section and len(results) < max_items:
                url = f"{base_api}?filter%5Bcategory_id%5D={sec_id}&page={page}"
                try:
                    req = urllib.request.Request(url, headers=self.headers)
                    with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=12) as resp:
                        js = json.loads(resp.read().decode('utf-8'))
                        data = js.get("data", [])
                        if not data:
                            break

                        for item in data:
                            if len(results) >= max_items or sec_added >= items_per_section:
                                break

                            urls = item.get("urls", {})
                            orig_url = urls.get("original") or item.get("image_url")
                            if not orig_url:
                                continue

                            # Prefer optimized web thumbnail (462px height or 235px)
                            thumb_url = urls.get("h462") or urls.get("h235") or orig_url
                            caption = item.get("caption") or f"{sec_name} - لقطة {item.get('id')}"
                            w = item.get("width", 1920)
                            h = item.get("height", 1080)

                            disc = DiscoveredItem(
                                source_id=self.source_id,
                                source_name=self.source_name,
                                source_page=f"https://pic.alkafeel.net/sections/{sec_id}?lang=ar",
                                original_url=orig_url,
                                thumbnail_url=thumb_url,
                                title=caption.strip(),
                                category=sec_cat,
                                shrine=sec_shrine,
                                license_text=self.license_text
                            )
                            # Attach dimensions to item for fast indexing
                            disc.width = w
                            disc.height = h
                            disc.item_id = f"alkafeel_{item.get('id')}"

                            results.append(disc)
                            sec_added += 1

                        if page >= js.get("last_page", 1):
                            break
                        page += 1
                        time.sleep(0.15)
                except Exception as e:
                    print(f"[AlKafeelAdapter] Error fetching sec {sec_id} page {page}: {e}")
                    break

        print(f"[AlKafeelAdapter] Total items discovered: {len(results)}")
        return results
