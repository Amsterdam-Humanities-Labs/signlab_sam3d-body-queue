# signlab_s3b_server
Work queue that hands studio recordings to an off-site SAM 3D Body GPU worker and takes the reconstructions back.

## What it does
- `index.php`: next jobs; up to 1000 `.mp4` in `studioFilesMini/raw/` with no `.sam3dbody` and no `.s3b_lock`, prioritised `M20…` > `M…` > `L`/`R` > `A`/`B`, shuffled per band; skips >20 MB, `(` and `_h264`.
- `lockFile.php`: claims a take by writing `<take>.s3b_lock` (refuses if lock or result exists).
- `upload.php`: accepts `<take>.sam3dbody` into the same dir. `list_uploads.php`, `get_sam3dbody_files.php`: JSON listings.
- `lockFile.php` and `upload.php` (the two writers) need header `X-Api-Token: <S3B_WORKER_TOKEN>` (`auth.php`); the three read-only listings stay open.
- Leftovers from the HAMER research: `top50.html` (+ `mod.js`, needs untracked `top50_hand_clusters.json`, 346 MB) and `hand_mesh.html` (CSS 3D hand).
- 56,036 `.sam3dbody` results exist, newest Feb 2026. The clustering scripts were removed; see git history.

## Where it runs
core (production): `/web/s3b_server`, https://signcollect.nl/s3b_server/. Not on the demo hosts.

## Status
experimental (whether the GPU worker still polls is unknown; it must now send `X-Api-Token`)

## How to run / deploy
Not in repos.tsv; copy the tree to `/web/s3b_server`. No build step, nothing here needs to be writable.

## Configuration
- `S3B_WORKER_TOKEN`: in the signcollect-lib env file (`/web/.env`) when `/web/lib` exists, else Apache `SetEnv`. Unset = writers refuse everything.
- `<root>/gebarenoverleg_media/studioFilesMini/raw/` in all PHP endpoints; `<root>` comes from vendored `sc_paths.php` (from signlab_signcollect-lib; edit it there): `SC_WEB_ROOT`, default `/web`.

## Dependencies
- `studioFilesMini/raw/`, shared with signlab_s3b_viewer (browses results) and signlab_s3b_glb (VTT sidecars).
- External GPU worker running Meta's SAM 3D Body; its code is in no signlab repo.
