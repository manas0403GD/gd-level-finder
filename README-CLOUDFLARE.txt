GD LEVEL FINDER — CLOUDFLARE PAGES + D1

This package preserves the existing static interface and moves its Flask API to Cloudflare Pages Functions.
The live database is Cloudflare D1.

1) Create a Cloudflare Pages project connected to the GitHub repository.
2) Set the Pages root/build output directory to public (build command can be blank).
3) Create a D1 database named gd-level-finder-db.
4) In Pages > Settings > Functions > D1 database bindings, add binding name DB and select that database.
5) Import d1-schema-and-seed.sql into the D1 database using the D1 Console or Wrangler.
6) Deploy Pages again. Check /api/status and /api/levels.

IMPORTANT:
- This is a Cloudflare Pages project root layout. Move public/* to the repo root's public folder, and functions/ plus wrangler.toml to repo root.
- Do NOT deploy the old gdlf.sqlite3 file.
- Personal collections/profile/settings remain browser-local by design.
- Community ideas are stored in shared D1.
- API endpoints: /api/status, /api/levels, /api/ideas, /api/list-data.
- No AREPL endpoint is included.
