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

    def download_image_bytes(self, url: str, timeout: int = 25) -> bytes:
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=timeout) as resp:
            return resp.read()

    def process_item(self, item: DiscoveredItem, known_hashes: set) -> dict:
        """
        Downloads, verifies, creates webp image and thumbnail, computes hash.
        Returns wallpaper record dict or None if duplicate/invalid.
        """
        raw_bytes = self.download_image_bytes(item.original_url)
        if not raw_bytes or len(raw_bytes) < 1024:
            raise ValueError(f"Downloaded file too small ({len(raw_bytes)} bytes)")

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        if sha256_hash in known_hashes:
            return {"status": "duplicate", "sha256": sha256_hash}

        # Open image with Pillow to validate
        img = Image.open(io.BytesIO(raw_bytes))
        img.verify()
        # Re-open for processing after verify
        img = Image.open(io.BytesIO(raw_bytes))

        # Convert palette/RGBA modes to RGB for clean WebP
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = rgb_img
        elif img.mode != "RGB":
            img = img.convert("RGB")

        orig_width, orig_height = img.size
        # Minimum resolution check (avoid icons/buttons)
        if orig_width < 400 or orig_height < 400:
            raise ValueError(f"Image resolution too low ({orig_width}x{orig_height})")

        # Generate unique item id based on source and hash
        item_id = f"wp_{sha256_hash[:16]}"
        filename = f"{item_id}.webp"
        thumb_filename = f"{item_id}_thumb.webp"

        image_path = os.path.join(self.images_dir, filename)
        thumb_path = os.path.join(self.thumbs_dir, thumb_filename)

        # 1. Save optimized full-size / high-res mobile WebP
        # If dimensions are huge (e.g. > 3840), resize preserving aspect ratio
        max_dimension = 3840
        if max(orig_width, orig_height) > max_dimension:
            scale = max_dimension / max(orig_width, orig_height)
            new_size = (int(orig_width * scale), int(orig_height * scale))
            full_img = img.resize(new_size, Image.Resampling.LANCZOS)
        else:
            full_img = img

        full_img.save(image_path, "WEBP", quality=88, method=6)
        file_size = os.path.getsize(image_path)
        final_w, final_h = full_img.size

        # 2. Save thumbnail WebP (max 480px on longest side for instant grid loading)
        thumb_img = img.copy()
        thumb_img.thumbnail((480, 480), Image.Resampling.LANCZOS)
        thumb_img.save(thumb_path, "WEBP", quality=80, method=4)

        # Base CDN/Raw URLs for direct public access without GitHub login
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
            "file_size": file_size,
            "width": final_w,
            "height": final_h,
            "date_added": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sha256": sha256_hash
        }
        return {"status": "success", "record": record}
