import open3d as o3d
import numpy as np
import tkinter as tk
import os
from tkinter import filedialog
import time

SUPPORTED = {".stl", ".obj", ".ply", ".gltf", ".glb"}

def load_mesh_from_path(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported format: {ext}")
    mesh = o3d.io.read_triangle_mesh(path)
    if len(mesh.triangles) == 0:
        raise ValueError(f"{path} has no triangles — possibly a point cloud, not a mesh")
    mesh.translate(-mesh.get_center())
    return mesh

def create_scene(mesh):
    scene = o3d.visualization.Visualizer()
    scene.create_window()
    scene.add_geometry(mesh)
    return scene

def pick_file():
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename(title="Select Mesh file", filetypes=[
    ("All supported", "*.stl *.STL *.obj *.OBJ *.ply *.PLY *.gltf *.glb"),
    ("STL files", "*.stl *.STL"),
    ("OBJ files", "*.obj *.OBJ"),
    ("PLY files", "*.ply *.PLY"),
    ("glTF files", "*.gltf *.glb"),
])
    return file_path
    
def make_camera_pass(bbox):
    center = bbox.get_center()
    extent = bbox.get_extent()
    radius = np.linalg.norm(extent) * 1.5  # Set radius based on the size of the bounding box
    angles = np.linspace(0, 2 * np.pi, num=36)  # 36 views around the object
    camera_positions = []
    
    for angle in angles:
        x = center[0] + radius * np.cos(angle)
        y = center[1] + radius * np.sin(angle)
        z = center[2] + radius * 0.5  # Slightly above the object
        camera_positions.append((x, y, z))
    
    return camera_positions


def positions_to_spheres(camera_positions):
    spheres = []
    for pos in camera_positions:
        sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.05)
        sphere.translate(pos)
        spheres.append(sphere)
    return spheres

def cast_all(camera_positions, mesh):
    mesh_t = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(mesh_t)
    
    all_points = []
    
    for pos in camera_positions:
        rays = scene.create_rays_pinhole(
            fov_deg=60,
            center=mesh.get_center(),
            eye=np.array(pos),
            up=[0, 0, 1],
            width_px=320,
            height_px=320
        )
        ans = scene.cast_rays(rays)  
        hit = ans['t_hit'].numpy()           
        dirs = rays.numpy()                 
        points = dirs[..., :3] + dirs[..., 3:] * hit[..., None]
        valid = np.isfinite(hit)
        points = points[valid]
        if points.size > 0:
            all_points.append(points)
    return np.concatenate(all_points)

def cast_for_one(camera_position, mesh):
    mesh_t = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(mesh_t)
    
    all_points = []
    
    rays = scene.create_rays_pinhole(
        fov_deg=60,
        center=mesh.get_center(),
        eye=np.array(camera_position),
        up=[0, 0, 1],
        width_px=320,
        height_px=320
    )
    ans = scene.cast_rays(rays)  
    hit = ans['t_hit'].numpy()           
    dirs = rays.numpy()                 
    points = dirs[..., :3] + dirs[..., 3:] * hit[..., None]
    valid = np.isfinite(hit)
    points = points[valid]
    if points.size > 0:
        all_points.append(points)
    return np.concatenate(all_points)

def main():
    path = pick_file()
    mesh = load_mesh_from_path(path)
    bbox = mesh.get_axis_aligned_bounding_box()
    camera_positions = make_camera_pass(bbox)
    # points = cast_all(camera_positions, mesh)
    # pcd.points = o3d.utility.Vector3dVector(points)
    
    pcd = o3d.geometry.PointCloud()
    vis = create_scene(mesh)
    spheres = positions_to_spheres(camera_positions)
    for sphere in spheres:
        vis.add_geometry(sphere)
    vis.add_geometry(pcd)

    sum_of_points = np.empty((0, 3))
    mesh_t = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    for cam_pos in camera_positions:
        all_points = []
        scene.add_triangles(mesh_t)
        rays = scene.create_rays_pinhole(
            fov_deg=60,
            center=mesh.get_center(),
            eye=np.array(cam_pos),
            up=[0, 0, 1],
            width_px=64,
            height_px=64
        )
        ans = scene.cast_rays(rays)  
        hit = ans['t_hit'].numpy()           
        dirs = rays.numpy()                 
        points = dirs[..., :3] + dirs[..., 3:] * hit[..., None]
        valid = np.isfinite(hit)
        points = points[valid]
        if points.size > 0:
            all_points.append(points)
            np.concatenate(all_points)
        
        sum_of_points = np.concatenate([sum_of_points] + all_points)
        pcd.points = o3d.utility.Vector3dVector(sum_of_points)
        vis.update_geometry(pcd)
        vis.poll_events()
        vis.update_renderer()
        time.sleep(0.1)  # Adjust delay as needed for visualization

    vis.run()
    vis.destroy_window()
    output_path = os.path.splitext(path)[0] + ".ply"
    o3d.io.write_point_cloud(output_path, pcd)


if __name__ == "__main__":
    main()
    