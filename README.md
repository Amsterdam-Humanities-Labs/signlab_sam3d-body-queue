# signlab_s3b_viewer
Three.js viewer for `.sam3dbody` reconstructions, played beside the source video.

## What it does
- `viewer.html`: unzips a `.sam3dbody` (JSZip), parses `body_keypoints_3d.npy`, animates the skeleton in sync with the video. Play/pause, timeline, 24/30/60 fps, 0.25-2x speed, loop, smoothing, mute.
- Load by drag-and-drop or from the sidebar.
- `api/files.php`: globs `*.sam3dbody`, builds a year/month/day tree (56,036 takes, newest Feb 2026), caches `api/cache.json` for 7 days.

## Where it runs
core (production): `/web/s3b_viewer`, https://signcollect.nl/s3b_viewer/viewer.html. Not on the demo hosts.

## Status
experimental

## How to run / deploy
Not in repos.tsv; copy the tree to an Apache+PHP dir; `api/` must be writable for `cache.json` (delete it to force a rescan). Locally, any static server plus drag-and-drop works.

## Configuration
Hardcoded: `/web/gebarenoverleg_media/studioFilesMini/raw/` (`api/files.php`), `/gebarenoverleg_media/studioFilesMini/raw/<take>.sam3dbody` and `https://media.signcollect.nl/<take>.mp4` (`viewer.html`).

## Dependencies
`.sam3dbody` files from the signlab_s3b_server pipeline; `media.signcollect.nl`; JSZip 3.10.1 (cdnjs) and three.js 0.160.0 (unpkg) in the browser.
