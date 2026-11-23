import os
import hashlib
import io
import time
from datetime import datetime, timezone
import urllib.request
import ssl
from PIL import Image
from adapters.base import DiscoveredItem

class ImageProcessor:
    def __init__(self, repo_owner: str, repo_name: str, images_dir: str, thumbs_dir: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.images_dir = images_dir
        self.thumbs_dir = thumbs_dir
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(thumbs_dir, exist_ok=True)

        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def process_item(self, item: DiscoveredItem, known_hashes: set) -> dict:
        """
        Processes discovered wallpaper item.
        Handles both direct verified CDN entries and downloadable items.
        """
        # If item already has verified dimensions and CDN thumbnail (e.g. AlKafeel API)
        if hasattr(item, 'width') and hasattr(item, 'height') and item.width and item.height:
            url_hash = hashlib.sha256(item.original_url.encode('utf-8')).hexdigest()
            if url_hash in known_hashes:
                return {"status": "duplicate", "sha256": url_hash}

            item_id = getattr(item, 'item_id', f"wp_{url_hash[:16]}")
            record = {
                "id": item_id,
                "title": item.title,
                "category": item.category,
                "shrine": item.shrine,
                "image_url": item.original_url,
                "thumbnail_url": item.thumbnail_url,
                "original_url": item.original_url,
                "source_name": item.source_name,
                "source_page": item.source_page,
                "license": item.license_text,
                "file_size": 0,
                "width": int(item.width),
                "height": int(item.height),
                "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sha256": url_hash
            }
            return {"status": "success", "record": record}

        # Otherwise download, probe, and optimize
        req = urllib.request.Request(item.original_url, headers=self.headers)
        with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=20) as resp:
            raw_bytes = resp.read()

        if not raw_bytes or len(raw_bytes) < 1024:
            raise ValueError(f"Downloaded file too small ({len(raw_bytes)} bytes)")

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        if sha256_hash in known_hashes:
            return {"status": "duplicate", "sha256": sha256_hash}

        img = Image.open(io.BytesIO(raw_bytes))
        orig_width, orig_height = img.size

        item_id = f"wp_{sha256_hash[:16]}"
        filename = f"{item_id}.webp"
        thumb_filename = f"{item_id}_thumb.webp"

        image_path = os.path.join(self.images_dir, filename)
        thumb_path = os.path.join(self.thumbs_dir, thumb_filename)

        # Save mobile optimized WebP
        if not os.path.exists(image_path):
            if img.mode != "RGB":
                img = img.convert("RGB")
            max_dimension = 3840
            if max(orig_width, orig_height) > max_dimension:
                scale = max_dimension / max(orig_width, orig_height)
                new_size = (int(orig_width * scale), int(orig_height * scale))
                full_img = img.resize(new_size, Image.Resampling.LANCZOS)
            else:
                full_img = img
            full_img.save(image_path, "WEBP", quality=88, method=6)

        if not os.path.exists(thumb_path):
            thumb_img = img.copy()
            thumb_img.thumbnail((480, 480), Image.Resampling.LANCZOS)
            thumb_img.save(thumb_path, "WEBP", quality=80, method=4)

        base_raw_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main"
        cdn_image_url = f"{base_raw_url}/images/{filename}"
        cdn_thumb_url = f"{base_raw_url}/thumbnails/{thumb_filename}"

        record = {
            "id": item_id,
            "title": item.title,
            "category": item.category,
            "shrine": item.shrine,
            "image_url": cdn_image_url,
            "thumbnail_url": cdn_thumb_url,
            "original_url": item.original_url,
            "source_name": item.source_name,
            "source_page": item.source_page,
            "license": item.license_text,
            "file_size": len(raw_bytes),
            "width": orig_width,
            "height": orig_height,
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sha256": sha256_hash
        }
        return {"status": "success", "record": record}
