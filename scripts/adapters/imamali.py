from typing import List
import re
import time
from bs4 import BeautifulSoup
from .base import BaseAdapter, DiscoveredItem

class ImamAliAdapter(BaseAdapter):
    """
    Adapter for media.imamali.net
    Traverses main shrine sections, extracts sub-albums, and iterates over pagination.
    """

    EXCLUDED_IDS = {319, 322, 323, 324, 325, 6901, 7403, 7477, 8840, 12966, 4172, 14631, 6049, 7755, 6056, 6096, 3203, 3284, 326, 993}

    def discover_wallpapers(self, max_items: int = 100) -> List[DiscoveredItem]:
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
                time.sleep(0.5)
            except Exception as e:
                print(f"[ImamAliAdapter] Error fetching section {sec_id}: {e}")
                continue

            # Find all sub-albums
            sub_albums = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if href.startswith('?id=') and href[4:].isdigit():
                    aid = int(href[4:])
                    if aid not in self.EXCLUDED_IDS and aid != sec_id:
                        title = a.get_text(strip=True)
                        # Clean numbers in front of title e.g. ١صور فنية
                        clean_title = re.sub(r'^[٠-٩0-9]+', '', title).strip()
                        sub_albums.append((aid, clean_title or title))

            print(f"[ImamAliAdapter] Found {len(sub_albums)} albums in {sec_name}")

            for album_id, album_title in sub_albums:
                if len(results) >= max_items:
                    break

                # Scan album pages (up to 3 pages per album to ensure balanced diversity)
                for page_num in range(1, 4):
                    if len(results) >= max_items:
                        break

                    album_page_url = f"{base_url}/?id={album_id}&p={page_num}"
                    try:
                        alb_html = self.fetch_text(album_page_url)
                        alb_soup = BeautifulSoup(alb_html, 'html.parser')
                        time.sleep(0.4)
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
                            # Full resolution image URL from files root
                            orig_url = f"https://imamali.net/files/{file_rel}"
                            thumb_url = f"{base_url}/{src}"
                            alt = img_el.get('alt', '')
                            clean_alt = alt.strip() if alt else f"{sec_name} - {album_title}"

                            # Determine specific category
                            category = sec_cat
                            if "عمارة" in album_title or "زخار" in album_title or "نقوش" in album_title:
                                category = "العمارة والزخارف الإسلامية"
                            elif "رمضان" in album_title or "محرم" in album_title or "عاشوراء" in album_title or "مواليد" in album_title or "وفيات" in album_title:
                                category = "المناسبات والفعاليات الدينية"

                            item = DiscoveredItem(
                                source_id=self.source_id,
                                source_name=self.source_name,
                                source_page=album_page_url,
                                original_url=orig_url,
                                thumbnail_url=thumb_url,
                                title=f"{clean_alt} ({album_title})",
                                category=category,
                                shrine=sec_shrine,
                                license_text=self.license_text
                            )
                            results.append(item)
                            found_in_page += 1

                    if found_in_page == 0:
                        # No more images in this album
                        break

        print(f"[ImamAliAdapter] Total items discovered: {len(results)}")
        return results
