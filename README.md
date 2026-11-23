# Islamic Shrines Wallpapers Library

Centralized wallpaper metadata and mobile API for Islamic Shrines.

## Project Structure
- .github/workflows/: Automation pipelines for periodic updates.
- data/: JSON index files for mobile applications.
  - wallpapers.json: Wallpaper catalog and links.
  - sources.json: Source configurations and categories.
  - ersion.json: Current catalog version for caching.
- scripts/: Modular extraction and indexing engine.
  - dapters/: Extensible adapters per source.
  - processor.py: Verification and image dimension parser.
  - scraper.py: Main execution CLI.

## Mobile API Usage
Mobile applications can consume the catalog directly:
- https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/wallpapers.json
- https://raw.githubusercontent.com/moshraheem-sudo/Islamic-Shrines-Wallpapers/main/data/version.json

## Manual Execution
To trigger workflow manually:
Navigate to Actions -> Auto Update Islamic Wallpapers -> Run workflow.
