from typing import List
import re
import time
from bs4 import BeautifulSoup
from .base import BaseAdapter, DiscoveredItem

class ImamAliAdapter(BaseAdapter):
    """
    Adapter for media.imamali.net
    Traverses main shrine sections, discovers all sub-albums, and iterates across pages.
    """

    MAIN_SECTIONS = {1367, 1368, 1369, 1370, 1371, 2095, 1407, 1408, 1372, 1373}
    EXCLUDED_IDS = {
        319, 322, 323, 324, 325, 6901, 7403, 7477, 8840, 12966, 4172, 14631, 
        6049, 7755, 6056, 6096, 3203, 3284, 326, 993, 1522, 1523, 1524, 1787, 
        2195, 1525, 1526, 1572, 3285, 15252, 15259, 15249, 15253
    }

    def discover_wallpapers(self, max_items: int = 200) -> List[DiscoveredItem]:
        results: List[DiscoveredItem] = []
        sections = self.config.get("sections", [])
        base_url = self.config.get("base_url", "https://media.imamali.net")

        for sec in sections:
            if len(results) >= max_items:
                break

            sec_id = sec.get("id")
            sec_name = sec.get("name", "العتبة العلوية المقدسة")
            sec_cat = sec.get("category", "العتبة العلوية المقدسة")
            sec_shrine = sec.get("shrine", sec_name)
            sec_url = f"{base_url}/?id={sec_id}"

            print(f"[ImamAliAdapter] Scanning shrine section: {sec_name} (ID: {sec_id})...")
            try:
                html = self.fetch_text(sec_url)
                soup = BeautifulSoup(html, 'html.parser')
                time.sleep(0.3)
            except Exception as e:
                print(f"[ImamAliAdapter] Error fetching section {sec_id}: {e}")
                continue

            # Find all legitimate sub-albums for this specific section
            sub_albums = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if href.startswith('?id=') and href[4:].isdigit():
                    aid = int(href[4:])
                    if aid not in self.EXCLUDED_IDS and aid not in self.MAIN_SECTIONS:
                        title = a.get_text(strip=True)
                        clean_title = re.sub(r'^[٠-٩0-9]+', '', title).strip()
                        clean_title = re.sub(r'[٠-٩0-9]+.*$', '', clean_title).strip()
                        sub_albums.append((aid, clean_title or title))

            print(f"[ImamAliAdapter] Found {len(sub_albums)} albums in {sec_name}")

            for album_id, album_title in sub_albums:
                if len(results) >= max_items:
                    break

                for page_num in range(1, 6):
                    if len(results) >= max_items:
                        break

                    album_page_url = f"{base_url}/?id={album_id}&p={page_num}"
                    try:
                        alb_html = self.fetch_text(album_page_url)
                        alb_soup = BeautifulSoup(alb_html, 'html.parser')
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"[ImamAliAdapter] Error fetching album {album_id} page {page_num}: {e}")
                        break

                    img_elements = alb_soup.find_all('img')
                    found_in_page = 0
                    for img_el in img_elements:
                        if len(results) >= max_items:
                            break
                        src = img_el.get('src', '')
                        if 'rpic.php?i=../files/' in src:
                            file_rel = src.split('i=../files/')[1].split('&')[0]
                            orig_url = f"https://imamali.net/files/{file_rel}"
                            thumb_url = f"{base_url}/{src}"
                            alt = img_el.get('alt', '')
                            clean_alt = alt.strip() if alt else f"{sec_name} - {album_title}"

                            category = sec_cat
                            if any(w in album_title for w in ["عمارة", "زخار", "نقوش", "ساعة", "منار", "قبة"]):
                                category = "العمارة والزخارف الإسلامية"
                            elif any(w in album_title for w in ["رمضان", "محرم", "عاشوراء", "مواليد", "وفيات"]):
                                category = "المناسبات والفعاليات الدينية"

                            item = DiscoveredItem(
                                source_id=self.source_id,
                                source_name=self.source_name,
                                source_page=album_page_url,
                                original_url=orig_url,
                                thumbnail_url=thumb_url,
                                title=f"{clean_alt} - {album_title}",
                                category=category,
                                shrine=sec_shrine,
                                license_text=self.license_text
                            )
                            results.append(item)
                            found_in_page += 1

                    if found_in_page == 0:
                        break

        print(f"[ImamAliAdapter] Total items discovered: {len(results)}")
        return results
