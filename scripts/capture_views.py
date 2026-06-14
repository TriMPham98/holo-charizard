"""
Capture EEVEE renders from multiple camera angles for holo verification.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/capture_views.py

Rebuild scene first:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/setup_holo_charizard.py
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/capture_views.py
"""

import os
import sys

import bpy
from mathutils import Vector

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_render_utils import configure_eevee_render

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLEND_PATH = os.path.join(PROJECT_ROOT, "holo_charizard.blend")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "renders")

CARD_HEIGHT = 8.8
CARD_FOCUS = Vector((0.0, 0.0, CARD_HEIGHT * 0.55))
STRESS_LIGHT_ENERGY_MULTIPLIER = 2.0


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def point_camera_at(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def get_camera():
    cam = bpy.data.objects.get("Camera")
    if cam is None:
        raise RuntimeError("Scene is missing Camera object.")
    return cam


def load_scene():
    if not os.path.isfile(BLEND_PATH):
        raise FileNotFoundError(
            f"Missing {BLEND_PATH}. Run scripts/setup_holo_charizard.py first."
        )
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)


def render_named_view(name, location, target=None):
    cam = get_camera()
    bpy.context.scene.camera = cam
    cam.location = Vector(location)
    point_camera_at(cam, target or CARD_FOCUS)

    output_path = os.path.join(RENDERS_DIR, f"{name}.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"✓ Rendered {output_path}")
    return output_path


def render_stress_bright():
    """Catch emission blowout regressions under brighter key lighting."""
    key = bpy.data.objects.get("KeyLight")
    if key is None:
        print("⚠ Skipping holo_stress_bright — KeyLight not found.")
        return None

    original_energy = key.data.energy
    key.data.energy = original_energy * STRESS_LIGHT_ENERGY_MULTIPLIER
    try:
        return render_named_view("holo_stress_bright", get_camera().location.copy())
    finally:
        key.data.energy = original_energy


def main():
    ensure_dir(RENDERS_DIR)
    load_scene()
    configure_eevee_render(bpy.context.scene, enable_compositor_bloom=True, png_output=True)

    default_cam = get_camera()
    default_location = default_cam.location.copy()

    views = [
        ("front_camera", tuple(default_location)),
        ("back_camera", (0.0, 12.0, 8.0)),
        ("holo_angle_left", (-5.5, -10.5, 7.0)),
        ("holo_angle_right", (5.5, -10.5, 7.0)),
    ]

    rendered = []
    for name, location in views:
        rendered.append(render_named_view(name, location))

    stress_path = render_stress_bright()
    if stress_path:
        rendered.append(stress_path)

    default_cam.location = default_location
    point_camera_at(default_cam, CARD_FOCUS)
    print("\nCaptured views:")
    for path in rendered:
        print(f"  {path}")


if __name__ == "__main__":
    main()