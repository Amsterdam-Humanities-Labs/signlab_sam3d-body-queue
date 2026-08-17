# mhr

Mesh/animation source assets for the MHR avatar.

## Contents (not in git)

The three files in this directory are binary assets that exceed GitHub's 100 MB
file limit, so they are excluded via `.gitignore` and live only on the server:

| File | Size |
|---|---|
| `animated_body.glb` | 456 MB |
| `mhr_animated.blend` | 136 MB |
| `lod0.fbx` | 29 MB |

To version these, set up [Git LFS](https://git-lfs.com/) on this repo and
`git lfs track "*.glb" "*.blend" "*.fbx"` before re-adding them.

Related: [`mhr_to_blender`](https://github.com/rem0g/mhr_to_blender).
