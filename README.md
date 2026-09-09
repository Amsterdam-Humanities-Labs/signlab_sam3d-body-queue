# s3b_server

The server side of the SAM 3D Body pipeline: a work queue that hands studio
recordings to an off-site GPU worker and takes the reconstructions back, plus
the hand-shape clustering scripts that were run over the results.

**Status: experimental.** See *Status* below before relying on anything here.

## What it does

Two things, from two different generations of the same research, living in one
directory.

**1. The SAM 3D Body work queue (PHP).** A GPU machine that cannot be reached
from here polls this directory over HTTP:

| Endpoint | Purpose |
|---|---|
| `index.php` | "What should I do next?" Lists up to 1000 `.mp4` in `studioFilesMini/raw/` that have neither a `.sam3dbody` result nor a `.s3b_lock`, prioritised `M20…` > `M…` > `L`/`R` > `A`/`B` > rest, shuffled within each band, skipping files over 20 MB and any name with a `(` or `_h264` in it. |
| `lockFile.php` | Claim one take by writing `<take>.s3b_lock` next to it. Refuses if the lock or the result already exists — this is the whole concurrency story. |
| `upload.php` | Accept the finished `<take>.sam3dbody` back into the same directory. |
| `list_uploads.php`, `get_sam3dbody_files.php` | Plain directory listings of the `.mp4` set, as JSON. |

There is no authentication on any of them and `upload.php` writes into the media
tree on an extension check alone.

**2. Hand-shape clustering (Python + static pages).** `cluster.py` clusters
per-frame finger-angle (or raw keypoint) vectors out of `.hamer` files —
k-means, DBSCAN, agglomerative or HDBSCAN, with Euclidean, Mahalanobis or a
weighted-combined distance, and LOF / isolation-forest / Mahalanobis outlier
filtering. `find_highest_count.py` takes the resulting
`angle_hand_clusters.json`, picks the 50 biggest clusters per hand, renders the
centroids as 3D plots, and writes `top50_hand_clusters.json` for `top50.html` to
browse. The committed PNGs in `centroids/` and `visualizations/` are that
script's output, kept as a record. `viewer.html` overlays a loaded `.hamer` file
on its video; `hand_mesh.html` is a pure-CSS 3D hand toy.

## Where it runs

The **signcollect core server** (production VPS), at `/web/s3b_server`, served as
<https://signcollect.nl/s3b_server/>.

It is **not** deployed to the demo hosts (dev2 `/web`, dev-1
`/srv/signcollect/web`) — nothing the demo portal can reach references it.

## Status

Experimental, and the two halves are in different states.

- The repository was created 2026-08-17 by importing a server directory that
  already existed. Its whole history is two housekeeping commits, so git tells
  you nothing about when any of this was written.
- **The queue produced real work.** There are 56,036 `.sam3dbody` files in the
  media tree, the newest dated February 2026. Whether the GPU worker still polls
  is not visible from here. *TODO: confirm whether the SAM 3D Body worker is
  still running against this endpoint.*
- **The clustering half is stale.** It reads `.hamer` files from an earlier
  HAMER hand-pose pipeline, not the `.sam3dbody` files the queue collects now.
  `viewer.html` fetches `get_hamer_files.php`, which does not exist in this
  repository (only `get_sam3dbody_files.php` does) and it handles the 404 by
  logging a warning. `find_highest_count.py` writes to `/web/hamer_server/…`,
  the directory's old name — that path is gone, so the script fails at the
  `os.makedirs` on any current host. Treat this half as a record of research
  already done rather than something that runs.

## Size and how to clone

The git repository is about **28 MB**, nearly all of it the 28 committed
centroid/visualisation PNGs. Clone it normally:

```bash
git clone git@github.com:Amsterdam-Humanities-Labs/signlab_s3b_server.git
```

If you only want the code, skip the pictures:

```bash
git clone --depth 1 --filter=blob:none --sparse git@github.com:Amsterdam-Humanities-Labs/signlab_s3b_server.git
cd signlab_s3b_server && git sparse-checkout set --no-cone '/*' '!/centroids' '!/visualizations'
```

The **~688 MB** figure people quote is the deployed directory, not the clone.
The difference is two untracked files that `.gitignore` excludes because GitHub
rejects them: `top50_hand_clusters.json` (346 MB) and `all_hand_clusters.json`
(346 MB), both outputs of the clustering run. You do not get them from a clone
and you do not need them unless you are reviving `top50.html`.

## Running it

The PHP side has no build step and no dependencies: copy the tree to
`/web/s3b_server` and make sure Apache can read it. Nothing here needs to be
writable — every write goes to the media directory instead.

The Python side is standalone:

```bash
pip install numpy scikit-learn scipy matplotlib tqdm   # hdbscan optional
python3 cluster.py /path/to/hamer_dir -o clusters.json --method kmeans -k 10 \
        --feature angle --distance mahalanobis --threads 8
python3 find_highest_count.py          # paths are hardcoded; see Status
```

## Configuration (not in git)

Nothing — there is no credentials file and no config file. The one thing that
must exist is the media directory, `/web/gebarenoverleg_media/studioFilesMini/raw/`,
hardcoded in all four PHP endpoints. On a host that does not have it, every
endpoint returns `{"error": "…directory not found or not readable."}`.

`top50_hand_clusters.json` and `all_hand_clusters.json` are likewise not in git;
they only exist where the clustering was run.

## Dependencies

- **`/web/gebarenoverleg_media/studioFilesMini/raw/`** — the studio recordings
  and their `.sam3dbody` results. Shared with `s3b_viewer` (which browses the
  results) and `s3b_glb` (which reads the `.vtt` sidecars).
- **An external GPU worker** running Meta's SAM 3D Body. It is not in this
  repository and not in this organisation. *TODO: confirm where that worker's
  code lives.*
- **HAMER** (`.hamer` files) for the clustering half — likewise external.
