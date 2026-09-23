# signlab_sam3d-body-queue/viewer
Three.js viewer that plays `.sam3dbody` reconstructions beside the source video. Until Sep 2026 this was the separate repo signlab_s3b_viewer.

## What it does
- `viewer.html` unzips a `.sam3dbody` (JSZip), parses `body_keypoints_3d.npy` and animates the skeleton in sync with the video.
- Controls: play/pause, timeline, 24/30/60 fps, speed 0.25-2x, loop, smoothing, mute.
- Load a file by drag-and-drop or from the sidebar.
- `api/files.php` finds all `*.sam3dbody` files and builds a year/month/day tree (56,036 recordings, newest Feb 2026). It caches the tree in `api/cache.json` for 7 days.

## Where it runs
Core server: `/web/s3b_viewer`, https://signcollect.nl/s3b_viewer/viewer.html (deployed from the old repo). Deploying signlab_sam3d-body-queue puts it at `/web/s3b_server/viewer/`. Not on the demo hosts.

## Status
Experimental.

## How to run / deploy
Copy the folder to an Apache + PHP directory. `api/` must be writable for `cache.json`; delete that file to force a rescan. Locally, any static server with drag-and-drop works.

## Configuration
- `api/files.php` reads `<root>/gebarenoverleg_media/studioFilesMini/raw/`. `<root>` comes from the vendored `sc_paths.php`: `SC_WEB_ROOT`, default `/web`. Edit it in [signlab_signcollect-lib](https://github.com/Amsterdam-Humanities-Labs/signlab_signcollect-lib), not here.
- Hardcoded in `viewer.html`: `/gebarenoverleg_media/studioFilesMini/raw/<take>.sam3dbody` and `https://media.signcollect.nl/<take>.mp4`.

## Dependencies
- `.sam3dbody` files from the queue in the parent folder (`../README.md`).
- Videos from `media.signcollect.nl`.
- In the browser: JSZip 3.10.1 (cdnjs) and three.js 0.160.0 (unpkg).
