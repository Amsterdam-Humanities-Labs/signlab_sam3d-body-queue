# signlab_sam3d-body-queue
Work queue that hands studio recordings to an off-site SAM 3D Body GPU worker and takes the reconstructions back.

## What it does
- `index.php` lists the next jobs: up to 1000 `.mp4` files in `studioFilesMini/raw/` with no `.sam3dbody` and no `.s3b_lock`. Priority is `M20…`, then `M…`, then `L`/`R`, then `A`/`B`, shuffled within each band. It skips files over 20 MB and names with `(` or `_h264`.
- `lockFile.php` (POST `filename=<take>.mp4`) claims a recording by writing `<take>.s3b_lock`. It refuses if a lock or result already exists.
- `upload.php` (POST, file field `sam3dbodyFile`) stores `<take>.sam3dbody` in the same folder.
- `list_videos.php` lists the `.mp4` names in that folder as JSON. `list_video_urls.php` adds their URLs and skips names starting with `#`. The old names `list_uploads.php` and `get_sam3dbody_files.php` remain as stubs.
- The two writers, `lockFile.php` and `upload.php`, need the header `X-Api-Token: <S3B_WORKER_TOKEN>` (`auth.php`). The three read-only listings stay open.
- `viewer/` browses the results (was signlab_s3b_viewer). `mhr/` holds notes on the MHR model (was signlab_mhr). Each has its own README.
- Left over from the HAMER research: `top50.html` (with `mod.js`; needs the untracked 346 MB `top50_hand_clusters.json`) and `hand_mesh.html` (CSS 3D hand). The clustering scripts are gone; see git history.
- 56,036 `.sam3dbody` results exist. The newest is from Feb 2026.

## Where it runs
Core server: `/web/s3b_server`, https://signcollect.nl/s3b_server/. Not on the demo hosts.

## Status
Experimental. Nobody knows whether the GPU worker still polls; it must now send `X-Api-Token`.

## How to run / deploy
`repos.tsv` does not list it. Copy the tree to `/web/s3b_server`. There is no build step. Only `viewer/api/` needs to be writable (see `viewer/README.md`).

## Configuration
- `S3B_WORKER_TOKEN`: in the signcollect-lib env file (`/web/.env`) when `/web/lib` exists, else an Apache `SetEnv`. If it is unset, the writers refuse every request.
- All PHP endpoints use `<root>/gebarenoverleg_media/studioFilesMini/raw/`. `<root>` comes from the vendored `sc_paths.php`: `SC_WEB_ROOT`, default `/web`. Edit it in [signlab_signcollect-lib](https://github.com/Amsterdam-Humanities-Labs/signlab_signcollect-lib), not here.

## Dependencies
- `studioFilesMini/raw/`, shared with `viewer/` and [signlab_body-animation-viewer](https://github.com/Amsterdam-Humanities-Labs/signlab_body-animation-viewer) (VTT sidecars).
- An external GPU worker running Meta's SAM 3D Body. Its code is in no signlab repo.

## License and citation

Apache License 2.0, copyright University of Amsterdam: see [LICENSE](LICENSE) and
[NOTICE](NOTICE). You may use it, also commercially, as long as you credit
Gomer Otterspeer / University of Amsterdam as the source. To cite it, use
[CITATION.cff](CITATION.cff) (the *Cite this repository* button on GitHub) or the DOI [10.21942/uva.33980371](https://doi.org/10.21942/uva.33980371).
