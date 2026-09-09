# mhr

Mesh and animation source assets for the MHR avatar — the artefacts of an
attempt to turn Meta's MHR body model into a rigged Blender character.

**Status: experimental, and not code.** This repository is a placeholder for a
directory whose entire contents are too large for GitHub. Everything it
describes lives on the server; nothing is versioned here.

## What it is

Three binaries, produced while trying to map SAM 3D Body's `mhr_parameters.npz`
onto MHR's rigged `lod0.fbx`:

| File | Size | What it is |
|---|---|---|
| `animated_body.glb` | 456 MB | The reconstruction as a sequence of PLY meshes — 160 frames at ~1.5 MB of mesh each. Not rigged: it is 100 % geometry, which is why it is this big. |
| `mhr_animated.blend` | 136 MB | The attempt to drive a rigged MHR character from `mhr_parameters`. |
| `lod0.fbx` | 29 MB | The rigged MHR character itself, from Meta's MHR release. |

The remapping problem these were made to investigate is written up at
<https://github.com/facebookresearch/sam-3d-body/issues/53>.

## Where it runs

Nothing runs. The files sit on the **signcollect core server** (production VPS)
at `/web/mhr`, and are served statically as `https://signcollect.nl/mhr/<file>`.

They are **not** deployed to the demo hosts (dev2 `/web`, dev-1
`/srv/signcollect/web`).

## Status

Experimental, and to the best available reading, **finished-and-parked** rather
than in progress:

- This repository has never held anything but a `.gitignore` and this README.
  It was created 2026-08-17; both commits are housekeeping.
- The related work, [`rem0g/mhr_to_blender`](https://github.com/rem0g/mhr_to_blender)
  ("An attempt to convert MHR to Blender character with rigged animation"), was
  last pushed in November 2025.
- The assets are still hosted and still downloadable.

*TODO: confirm whether the MHR-to-Blender conversion was abandoned or superseded
by another approach.*

## Getting the assets

**Git LFS is not set up on this repository.** There is no `.gitattributes`, no
LFS pointer file and no LFS object store — an earlier version of this README
suggested setting LFS up, and that suggestion was never acted on. Cloning gets
you this text and nothing else.

Download them over HTTP instead:

```bash
curl -O https://signcollect.nl/mhr/animated_body.glb    # 456 MB
curl -O https://signcollect.nl/mhr/mhr_animated.blend   # 136 MB
curl -O https://signcollect.nl/mhr/lod0.fbx             #  29 MB
```

That is ~621 MB in total, so fetch only the one you need. On the server itself
they are already in `/web/mhr` — copy from there rather than round-tripping
through HTTP.

If these ever do need to be versioned, LFS is the mechanism:

```bash
git lfs install
git lfs track "*.glb" "*.blend" "*.fbx"
git add .gitattributes && git commit -m "Track large binaries with Git LFS"
# then remove the three entries from .gitignore and add the files
```

Check the organisation's LFS storage quota first — 621 MB of history is not
free, and each new revision of `animated_body.glb` costs another 456 MB.

## Dependencies

- [`rem0g/mhr_to_blender`](https://github.com/rem0g/mhr_to_blender) — the
  conversion attempt these assets came out of. It carries the small inputs that
  are small enough to version: `mhr_parameters.npz`, `lod0_bone_names.json` and
  `keypoints_pointcloud.blend`.
- [Meta MHR](https://github.com/facebookresearch/MHR) — the source of `lod0.fbx`.
- [SAM 3D Body](https://github.com/facebookresearch/sam-3d-body) — the source of
  the `mhr_parameters.npz` the `.blend` tries to consume. The same model feeds
  the `s3b_*` repositories in this organisation.
- Blender, to open the `.blend`. *TODO: confirm which Blender version the file
  was authored in.*
