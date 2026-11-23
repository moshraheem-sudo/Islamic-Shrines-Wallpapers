import os
import json
import re

def slugify(text: str) -> str:
    slug_map = {
        "العتبة العلوية المقدسة": "alawi",
        "العتبة الحسينية المقدسة": "hussaini",
        "العتبة العباسية المقدسة": "abbasi",
        "العتبة الكاظمية المقدسة": "kadhimi",
        "العتبة العسكرية المقدسة": "askari",
        "العتبة الرضوية المقدسة": "ridhawi",
        "المراقد والمزارات الإسلامية": "shrines",
        "العمارة والزخارف الإسلامية": "architecture",
        "المناسبات والفعاليات الدينية": "events"
    }
    if text in slug_map:
        return slug_map[text]
    # Clean text fallback
    cleaned = re.sub(r'[^\w\s-]', '', text).strip().replace(' ', '_')
    return cleaned or "other"

def export_paginated_and_categories(base_dir: str, wallpapers: list, per_page: int = 50):
    data_dir = os.path.join(base_dir, "data")
    pages_dir = os.path.join(data_dir, "pages")
    cats_dir = os.path.join(data_dir, "categories")
    
    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(cats_dir, exist_ok=True)

    total_items = len(wallpapers)
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1

    # 1. Export Pages
    for p in range(1, total_pages + 1):
        start = (p - 1) * per_page
        end = start + per_page
        page_items = wallpapers[start:end]
        page_file = os.path.join(pages_dir, f"page_{p}.json")
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump({
                "page": p,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total_items,
                "items": page_items
            }, f, ensure_ascii=False, indent=2)

    # Pages Index
    with open(os.path.join(pages_dir, "index.json"), 'w', encoding='utf-8') as f:
        json.dump({
            "total_items": total_items,
            "per_page": per_page,
            "total_pages": total_pages,
            "pages_urls": [f"pages/page_{p}.json" for p in range(1, total_pages + 1)]
        }, f, ensure_ascii=False, indent=2)

    # 2. Export Categories
    by_category = {}
    for wp in wallpapers:
        cat = wp.get("category", "غير مصنف")
        by_category.setdefault(cat, []).append(wp)

    categories_manifest = []
    for cat_name, items in by_category.items():
        slug = slugify(cat_name)
        cat_file = os.path.join(cats_dir, f"{slug}.json")
        with open(cat_file, 'w', encoding='utf-8') as f:
            json.dump({
                "category": cat_name,
                "slug": slug,
                "total_items": len(items),
                "items": items
            }, f, ensure_ascii=False, indent=2)

        categories_manifest.append({
            "category": cat_name,
            "slug": slug,
            "count": len(items),
            "file": f"categories/{slug}.json"
        })

    with open(os.path.join(cats_dir, "index.json"), 'w', encoding='utf-8') as f:
        json.dump({
            "total_categories": len(categories_manifest),
            "categories": categories_manifest
        }, f, ensure_ascii=False, indent=2)

    print(f"[Exporter] Successfully exported {total_pages} pages and {len(categories_manifest)} categories.")
