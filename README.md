# Virtual Point Cloud Scanner

Minimal pipeline for generating synthetic point clouds from CAD models via raycasting.

Simulates how an industrial scanner (e.g. Gocator) would capture a part from a specific scanning angle, producing a point cloud that reflects sensor visibility, occlusion, and scanner pose.

Built as a public minimal version of a production tool I use for testing point cloud matching algorithms in industrial welding robotics.

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate.py
```

A file picker will open — select your STL file. The script will:

1. Place cameras in a circular pass around the part
2. Simulate the scan via raycasting
3. Display the resulting point cloud overlaid on the mesh
4. Save the point cloud as a `.ply` file in the same directory as the input STL

## Screenshots

| Select STL | Raycasting on mesh | Final point cloud |
|:-----------:|:------------------:|:-----------------:|
| <img src="screenshots/select_stl.png" width="250"/> | <img src="screenshots/raycast_on_stl.png" width="250"/> | <img src="screenshots/final_ply.png" width="250"/> |

## Design choices

### Raycasting vs. uniform sampling

Uniform sampling from the mesh produces a point cloud over the entire surface of the object, regardless of whether those surfaces would be visible to a real scanner. For example, for an H-beam it would generate points on both flanges, the web, the top, the bottom, and even areas that would be hidden from the sensor. The result is a complete point cloud wrapping the whole mesh, which is useful for representing geometry but unrealistic as a simulated scan.

A real scanner only captures surfaces visible from its current position and field of view. If the beam is lying on a surface, the scanner will not capture the lower side; if a region is occluded by the part's own geometry, it will also be missing. Raycasting reproduces this behavior by casting rays from the scanner pose and keeping only the first visible intersections. The result is closer to real sensor data: it avoids points from surfaces a real scanner could never see, which would otherwise mislead downstream registration methods such as ICP.