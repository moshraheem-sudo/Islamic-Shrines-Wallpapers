from typing import List
import re
import time
from bs4 import BeautifulSoup
from .base import BaseAdapter, DiscoveredItem

class ImamAliAdapter(BaseAdapter):
    """
    Adapter for media.imamali.net
    Scans specified albums directly and iterates across all pages.
    """

    TARGET_ALBUMS = [
        (4026, "الضريح المقدس", "العتبة العلوية المقدسة"),
        (1374, "الحرم المطهر", "العتبة العلوية المقدسة"),
        (4410, "القبة الشريفة", "العتبة العلوية المقدسة"),
        (14810, "المنارتان الذهبيتان", "العتبة العلوية المقدسة"),
        (14813, "الساعة", "العتبة العلوية المقدسة"),
        (1376, "معالم عمرانية", "العمارة والزخارف الإسلامية"),
        (1375, "المرقد بين الحاضر والماضي", "العتبة العلوية المقدسة"),
        (15179, "صور فنية", "العتبة العلوية المقدسة"),
        (1175, "صور فائقة الدقة", "العتبة العلوية المقدسة"),
        (14848, "صحن السيدة فاطمة الزهراء", "العتبة العلوية المقدسة")
    ]

    def discover_wallpapers(self, max_items: int = 250) -> List[DiscoveredItem]:
        results: List[DiscoveredItem] = []
        base_url = self.config.get("base_url", "https://media.imamali.net")
        items_per_album = max(20, max_items // len(self.TARGET_ALBUMS))

        for album_id, album_name, cat_name in self.TARGET_ALBUMS:
            if len(results) >= max_items:
                break

            print(f"[ImamAliAdapter] Scanning targeted album: {album_name} (ID: {album_id})...")
            album_added = 0

            for page_num in range(1, 10):
                if len(results) >= max_items or album_added >= items_per_album:
                    break

                page_url = f"{base_url}/?id={album_id}&p={page_num}"
                try:
                    alb_html = self.fetch_text(page_url)
                    alb_soup = BeautifulSoup(alb_html, 'html.parser')
                    time.sleep(0.15)
                except Exception as e:
                    print(f"[ImamAliAdapter] Error fetching album {album_id} p={page_num}: {e}")
                    break

                img_elements = alb_soup.find_all('img')
                found_in_page = 0
                for img_el in img_elements:
                    if len(results) >= max_items or album_added >= items_per_album:
                        break
                    src = img_el.get('src', '')
                    if 'rpic.php?i=../files/' in src:
                        file_rel = src.split('i=../files/')[1].split('&')[0]
                        orig_url = f"https://imamali.net/files/{file_rel}"
                        thumb_url = f"{base_url}/{src}"
                        alt = img_el.get('alt', '')
                        title = alt.strip() if alt else f"العتبة العلوية المقدسة - {album_name}"

                        item = DiscoveredItem(
                            source_id=self.source_id,
                            source_name=self.source_name,
                            source_page=page_url,
                            original_url=orig_url,
                            thumbnail_url=thumb_url,
                            title=f"{title} ({album_name})",
                            category=cat_name,
                            shrine="مرقد الإمام علي بن أبي طالب (ع) - النجف الأشرف",
                            license_text=self.license_text
                        )
                        results.append(item)
                        album_added += 1
                        found_in_page += 1

                if found_in_page == 0:
                    break

        print(f"[ImamAliAdapter] Total items discovered: {len(results)}")
        return results
