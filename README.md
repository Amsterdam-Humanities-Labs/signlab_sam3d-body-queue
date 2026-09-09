# s3b_viewer

A standalone browser viewer for `.sam3dbody` reconstructions, played back beside
the video they came from.

**Status: experimental.** See *Status* below before relying on anything here.

## What it does

Two files. `viewer.html` is a single self-contained Three.js page; `api/files.php`
is the only server code.

The page renders the 3D body keypoints of a `.sam3dbody` file as an animated
skeleton, in a split view next to the source recording, with the two kept in
sync. Controls: play/pause, a frame timeline, 24/30/60 fps, 0.25×–2× speed,
loop, four levels of temporal smoothing, and audio mute.

A `.sam3dbody` file is a zip: the viewer opens it with JSZip, pulls out
`body_keypoints_3d.npy`, and parses the NumPy array in JavaScript (there is a
small hand-written `.npy` header parser in the page). Files arrive either by
drag-and-drop from your machine, or from the sidebar.

`api/files.php` builds that sidebar. It globs `*.sam3dbody` out of the media
directory, parses the `<letter>YYYYMMDD_NNNN` naming convention into a
year → month → day → takes tree, newest first, and caches the JSON for 7 days.
The tree is currently 56,036 takes.

## Where it runs

The **signcollect core server** (production VPS), at `/web/s3b_viewer`, served as
<https://signcollect.nl/s3b_viewer/viewer.html>.

It is **not** deployed to the demo hosts (dev2 `/web`, dev-1
`/srv/signcollect/web`) — nothing the demo portal can reach references it.

## Status

Experimental — a small tool that works, with no history and no owner visible in
the repository.

- The repository was created 2026-08-17 from a directory that already existed on
  the server; both commits are housekeeping. Nothing about the code's age or its
  last real change can be read out of git.
- It responds correctly on production today: the file API answers and the viewer
  loads.
- Nothing links to it. It is reached by typing the URL.
- The newest take in the index is from February 2026, which is when the
  `.sam3dbody` pipeline in `s3b_server` last produced output.

Expect prototype-grade code: one 932-line HTML file, no tests, no auth, no build
step, hardcoded absolute paths.

## Size and how to clone

Small — about **300 KB**. Clone it normally:

```bash
git clone git@github.com:Amsterdam-Humanities-Labs/signlab_s3b_viewer.git
```

Unlike its two siblings there is no large untracked payload in the deployed
directory either: this viewer reads everything out of the shared media tree.

## Running it

There is no build step and no dependency to install. Copy the tree to a
directory Apache serves, with PHP available, and make sure the web server can
write `api/cache.json` (gitignored; it is regenerated on the first request after
7 days, and that request is slow because it globs the whole media directory).

For local work, `viewer.html` opened over any static server is already useful —
drag a `.sam3dbody` onto it. The sidebar and the video pane need the server
paths below.

## Configuration (not in git)

There is no configuration file and no credentials. Three locations are
hardcoded, and this is what you edit to run it somewhere else:

| Hardcoded in | Value |
|---|---|
| `api/files.php` | `/web/gebarenoverleg_media/studioFilesMini/raw/` — where it globs for `.sam3dbody` |
| `viewer.html` | `/gebarenoverleg_media/studioFilesMini/raw/<take>.sam3dbody` — the URL it fetches a sidebar selection from |
| `viewer.html` | `https://media.signcollect.nl/<take>.mp4` — the reference video in the split view |

`api/cache.json` is generated and gitignored. Deleting it forces a rescan.

## Dependencies

- **`/web/gebarenoverleg_media/studioFilesMini/raw/`** — the `.sam3dbody` files,
  produced by the pipeline `s3b_server` feeds. Without them the sidebar is empty
  and drag-and-drop is the only way in.
- **`media.signcollect.nl`** for the reference video. If it is unreachable the
  3D playback still works; the video pane just stays blank.
- CDN, in the browser, unpinned to nothing local: JSZip 3.10.1 from
  cdnjs.cloudflare.com and **three.js 0.160.0 from unpkg.com** via an import map.
  Both need outbound internet from the client.
