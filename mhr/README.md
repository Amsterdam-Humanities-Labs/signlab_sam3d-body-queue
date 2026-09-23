# s3b_server/mhr
Notes on the MHR avatar files kept on the core server. No file is versioned here (no Git LFS). Until Sep 2026 this was the separate repo signlab_mhr.

## What it does
It records three files from an attempt to drive Meta's rigged MHR character with the `mhr_parameters.npz` output of SAM 3D Body (see https://github.com/facebookresearch/sam-3d-body/issues/53):

| File | Size | Content |
|---|---|---|
| `animated_body.glb` | 456 MB | the reconstruction as 160 unrigged mesh frames |
| `mhr_animated.blend` | 136 MB | the attempt to drive the rigged MHR character |
| `lod0.fbx` | 29 MB | the rigged MHR character from Meta's MHR release |

## Where it runs
Core server: `/web/mhr`, served at `https://signcollect.nl/mhr/<file>`. Not on the demo hosts.

## Status
Dormant (the conversion work was last pushed in Nov 2025).

## How to run / deploy
Nothing to run. To fetch one file:
```bash
curl -O https://signcollect.nl/mhr/lod0.fbx
```
Or copy it from `/web/mhr` on the server.

## Configuration
None.

## Dependencies
- Conversion code and small inputs: https://github.com/rem0g/mhr_to_blender.
- Sources: https://github.com/facebookresearch/MHR and SAM 3D Body.
- Blender, to open the `.blend` file.
