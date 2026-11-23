# Islamic Shrines Wallpapers Library

[![Auto Update Islamic Wallpapers](https://github.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/actions/workflows/update_wallpapers.yml/badge.svg)](https://github.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/actions/workflows/update_wallpapers.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An automated wallpaper metadata catalog and mobile API for Islamic shrine wallpapers, featuring scheduled discovery, deduplication, thumbnail generation, and multi-tier categorization via GitHub Actions.

## Highlights
- **Scalable Architecture**: Paginated JSON APIs (`data/pages/`) and category splits (`data/categories/`) to seamlessly handle 1,000+ wallpapers.
- **Dual-Tier Delivery**: High-speed lightweight thumbnails (`thumbnail_url`) for fluid mobile grid view, and high-resolution originals (`image_url`) for download.
- **Automated Ingestion**: GitHub Actions pipeline executes daily at 03:00 UTC to discover and index newly published items without duplicates (SHA-256 validation).
- **Direct Mobile Integration**: Public raw endpoints accessible by mobile apps without authentication.

## API Endpoints

### 1. Catalog & Versioning
- **Version & Cache Check**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/version.json`
- **Master Catalog (All Items)**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/wallpapers.json`

### 2. Paginated Endpoints (Lazy Loading)
- **Pages Index**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/pages/index.json`
- **Page 1 (50 items)**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/pages/page_1.json`

### 3. Categories Endpoints
- **Categories Index**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/categories/index.json`
- **Alawi Shrine**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/categories/alawi.json`
- **Askari Shrine**: `https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/categories/askari.json`

## Mobile Integration Example (Kotlin)

```kotlin
suspend fun fetchWallpapersPage(page: Int): List<WallpaperItem> = withContext(Dispatchers.IO) {
    val url = "https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/pages/page_$page.json"
    val json = URL(url).readText()
    val array = JSONObject(json).getJSONArray("items")
    (0 until array.length()).map { idx ->
        val obj = array.getJSONObject(idx)
        WallpaperItem(
            id = obj.getString("id"),
            title = obj.getString("title"),
            category = obj.getString("category"),
            imageUrl = obj.getString("image_url"),
            thumbnailUrl = obj.getString("thumbnail_url"),
            width = obj.getInt("width"),
            height = obj.getInt("height")
        )
    }
}
```

## Manual Execution
Trigger on-demand indexing via:
1. GitHub Repository -> **Actions** tab.
2. Select **Auto Update Islamic Wallpapers**.
3. Click **Run workflow** and specify batch size.
