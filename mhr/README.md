# signlab_mhr
Placeholder for the MHR avatar assets on the server; nothing is versioned here (no Git LFS).

## What it does
Records three binaries from an attempt to drive Meta's rigged MHR character with SAM 3D Body's `mhr_parameters.npz` (see https://github.com/facebookresearch/sam-3d-body/issues/53):

| File | Size | What |
|---|---|---|
| `animated_body.glb` | 456 MB | reconstruction as 160 unrigged mesh frames |
| `mhr_animated.blend` | 136 MB | attempt to drive the rigged MHR character |
| `lod0.fbx` | 29 MB | rigged MHR character from Meta's MHR release |

## Where it runs
core: `/web/mhr`, served at `https://signcollect.nl/mhr/<file>`. Not on the demo hosts.

## Status
dormant (conversion work last pushed Nov 2025)

## How to run / deploy
Nothing to run. Fetch one file: `curl -O https://signcollect.nl/mhr/lod0.fbx` (or copy from `/web/mhr` on the server).

## Dependencies
Conversion code and small inputs: https://github.com/rem0g/mhr_to_blender. Sources: https://github.com/facebookresearch/MHR, SAM 3D Body. Blender to open the `.blend`.
