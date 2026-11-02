GD LEVEL FINDER — FULLY PRELOADED OFFLINE DATABASE

This build includes the completed SQLite database with all 7,367 levels and their collected GDDL tag responses.

START:
1. Extract the entire ZIP into a folder.
2. Run START.bat.
3. The browser opens at http://127.0.0.1:5000.

No GDDL API key is required. No tag importer runs. Searching and filtering use the bundled local SQLite database only.

DATA CHECK:
- Levels: 7,367
- Tag-cache records: 7,367
- Non-empty GDDL tag lists: 6,925
- Empty GDDL tag lists: 442
- The 442 empty lists are stored API responses with no tags returned, not missing database records.

The website displays the two highest-reaction gamemode tags and the highest-reaction gameplay tag. The companion GD_Level_Finder_Master.csv contains every available tag and reaction count for all levels.

Keep gdlf.sqlite3 beside server.py. Do not remove it.
