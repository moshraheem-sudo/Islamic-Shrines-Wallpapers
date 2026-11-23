import os
import sys
import json
import argparse
from datetime import datetime, timezone
from adapters import get_adapter
from processor import ImageProcessor
from exporter import export_paginated_and_categories

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning reading {filepath}: {e}")
    return default

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Islamic Shrines Wallpapers Engine")
    parser.add_argument("--max-images", type=int, default=100, help="Max new images to discover/process per run")
    parser.add_argument("--source", type=str, default=None, help="Filter by specific source id")
    parser.add_argument("--repo-owner", type=str, default="moshraheem-sudo", help="GitHub repo owner")
    parser.add_argument("--repo-name", type=str, default="Islamic-Shrines-Wallpapers", help="GitHub repo name")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    sources_file = os.path.join(data_dir, "sources.json")
    wallpapers_file = os.path.join(data_dir, "wallpapers.json")
    version_file = os.path.join(data_dir, "version.json")
    stats_file = os.path.join(data_dir, "stats.json")
    logs_file = os.path.join(base_dir, "logs", "update_log.md")
    os.makedirs(os.path.dirname(logs_file), exist_ok=True)
    images_dir = os.path.join(base_dir, "images")
    thumbs_dir = os.path.join(base_dir, "thumbnails")

    sources_config = load_json(sources_file, {"sources": []})
    existing_wallpapers = load_json(wallpapers_file, [])
    version_info = load_json(version_file, {"version": 1, "total_wallpapers": 0})
    stats_info = load_json(stats_file, {"total_saved": 0, "by_category": {}, "by_source": {}})

    known_hashes = {w["sha256"] for w in existing_wallpapers if "sha256" in w}
    known_urls = {w["original_url"] for w in existing_wallpapers if "original_url" in w}

    processor = ImageProcessor(
        repo_owner=args.repo_owner,
        repo_name=args.repo_name,
        images_dir=images_dir,
        thumbs_dir=thumbs_dir
    )

    run_start = datetime.now(timezone.utc)
    new_added = 0
    duplicate_count = 0
    failed_count = 0

    sources_list = sources_config.get("sources", [])
    if args.source:
        sources_list = [s for s in sources_list if s.get("id") == args.source]

    print(f"=== Starting Islamic Shrines Scraper ===")
    print(f"Known wallpapers in database: {len(existing_wallpapers)}")
    print(f"Target max new images this run: {args.max_images}")

    for src in sources_list:
        if not src.get("enabled", True):
            continue

        src_id = src.get("id")
        adapter_cls_name = src.get("adapter")
        adapter_cls = get_adapter(adapter_cls_name)
        if not adapter_cls:
            print(f"Warning: Adapter {adapter_cls_name} not found for source {src_id}")
            continue

        adapter = adapter_cls(src)
        print(f"\n--- Running Source: {src.get('name')} ({src_id}) ---")

        try:
            discovered = adapter.discover_wallpapers(max_items=args.max_images)
        except Exception as e:
            print(f"Error during discovery for {src_id}: {e}")
            continue

        for item in discovered:
            if new_added >= args.max_images:
                break

            if item.original_url in known_urls:
                duplicate_count += 1
                continue

            try:
                result = processor.process_item(item, known_hashes)
                if result.get("status") == "duplicate":
                    duplicate_count += 1
                    known_hashes.add(result.get("sha256"))
                elif result.get("status") == "success":
                    record = result.get("record")
                    existing_wallpapers.append(record)
                    known_hashes.add(record["sha256"])
                    known_urls.add(record["original_url"])
                    new_added += 1

                    # Update stats
                    cat = record["category"]
                    s_name = record["source_name"]
                    stats_info.setdefault("by_category", {})[cat] = stats_info.get("by_category", {}).get(cat, 0) + 1
                    stats_info.setdefault("by_source", {})[s_name] = stats_info.get("by_source", {}).get(s_name, 0) + 1

                    print(f"  [+] Added ({new_added}/{args.max_images}): {record['title']} | {record['width']}x{record['height']}")
            except Exception as e:
                print(f"  [-] Skipped {item.original_url}: {e}")
                failed_count += 1

    run_end = datetime.now(timezone.utc)
    duration_sec = round((run_end - run_start).total_seconds(), 2)

    # Always export pages and categories for client efficiency
    export_paginated_and_categories(base_dir, existing_wallpapers, per_page=50)

    # Save wallpapers & version
    version_info["version"] = version_info.get("version", 0) + 1
    version_info["last_updated"] = run_end.strftime("%Y-%m-%dT%H:%M:%SZ")
    version_info["total_wallpapers"] = len(existing_wallpapers)
    save_json(wallpapers_file, existing_wallpapers)
    save_json(version_file, version_info)

    # Update stats
    stats_info["total_saved"] = len(existing_wallpapers)
    stats_info["last_run"] = {
        "timestamp": run_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": duration_sec,
        "new_added": new_added,
        "duplicates": duplicate_count,
        "failed": failed_count
    }
    save_json(stats_file, stats_info)

    # Append to log
    log_entry = (
        f"\n## Update Run: {run_end.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"- **New Wallpapers Added**: {new_added}\n"
        f"- **Duplicates Skipped**: {duplicate_count}\n"
        f"- **Failed / Skipped**: {failed_count}\n"
        f"- **Total Library Size**: {len(existing_wallpapers)}\n"
        f"- **Execution Time**: {duration_sec}s\n"
    )
    with open(logs_file, 'a', encoding='utf-8') as lf:
        lf.write(log_entry)

    print(f"\n=== Run Summary ===")
    print(f"Added: {new_added}, Duplicates: {duplicate_count}, Failed: {failed_count}")
    print(f"Total wallpapers in database: {len(existing_wallpapers)}")

if __name__ == '__main__':
    main()
