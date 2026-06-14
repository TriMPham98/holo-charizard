"""
Holo Charizard Card — Blender scene setup
Run: /Applications/Blender.app/Contents/MacOS/Blender --python scripts/setup_holo_charizard.py
Or open Blender → Scripting workspace → Run Script
"""

import math
import os
import subprocess
import sys

import bmesh
import bpy
from mathutils import Vector

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets", "textures")
BLEND_PATH = os.path.join(PROJECT_ROOT, "holo_charizard.blend")

# Card size in Blender units (~8 units tall so the default viewport can see it)
CARD_WIDTH = 6.3
CARD_HEIGHT = 8.8
CARD_THICKNESS = 0.032
CARD_CORNER_RADIUS = 0.32  # ~3.2 mm on a 63 mm-wide TCG card
CARD_CORNER_SEGMENTS = 12
CARD_LEAN_DEG = 10.0  # slight backward lean from vertical

# Holo art window (normalized UV bounds — classic card layout)
HOLO_UV_X_MIN = 0.08
HOLO_UV_X_MAX = 0.92
HOLO_UV_Y_MIN = 0.36
HOLO_UV_Y_MAX = 0.78


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.node_groups):
        for item in list(block):
            block.remove(item)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def add_interface_socket(group, name, in_out, socket_type, default=None):
    sock = group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    if default is not None and hasattr(sock, "default_value"):
        sock.default_value = default
    return sock


# ---------------------------------------------------------------------------
# Procedural textures
# ---------------------------------------------------------------------------
def generate_texture_files():
    script = os.path.join(PROJECT_ROOT, "scripts", "generate_textures.py")
    candidates = [
        os.environ.get("SYSTEM_PYTHON", ""),
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
        "/usr/bin/python3",
    ]
    for py in candidates:
        if py and os.path.isfile(py):
            subprocess.run([py, script], check=True)
            return
    raise RuntimeError(
        "Could not find system Python with Pillow. Run: python3 scripts/generate_textures.py"
    )


def load_image(name, colorspace="sRGB", extensions=(".png", ".jpg", ".jpeg")):
    path = None
    for ext in extensions:
        candidate = os.path.join(ASSETS_DIR, f"{name}{ext}")
        if os.path.isfile(candidate):
            path = candidate
            break
    if path is None:
        raise FileNotFoundError(f"Missing texture {name} in {ASSETS_DIR}")

    existing = bpy.data.images.get(name)
    if existing:
        bpy.data.images.remove(existing)
    img = bpy.data.images.load(path)
    img.name = name
    img.colorspace_settings.name = colorspace
    img.filepath = path
    img.reload()
    if len(img.pixels) > 0 and img.pixels[0] == 0.0:
        img.reload()
    if len(img.pixels) > 0 and sum(img.pixels[:12]) > 0.0:
        img.pack()
    return img


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------
def create_card_material(rainbow_img, dist_img, face_img, cosmos_img):
    for img in (face_img, rainbow_img, dist_img, cosmos_img):
        if img.pixels[0] == 0.0:
            img.reload()

    mat = bpy.data.materials.new("HoloCharizardCard")
    mat.use_nodes = True
    mat.use_backface_culling = True
    mat.diffuse_color = (0.95, 0.78, 0.12, 1.0)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (900, 0)

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1000, 200)

    face_tex = nodes.new("ShaderNodeTexImage")
    face_tex.location = (-750, 300)
    face_tex.image = face_img
    face_tex.interpolation = "Linear"

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (-200, 300)
    principled.inputs["Base Color"].default_value = (0.95, 0.78, 0.12, 1.0)
    principled.inputs["Roughness"].default_value = 0.22
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = 0.55

    layer = nodes.new("ShaderNodeLayerWeight")
    layer.location = (-1000, 0)
    layer.inputs["Blend"].default_value = 0.15

    geom = nodes.new("ShaderNodeNewGeometry")
    geom.location = (-1000, -200)

    view_neg = nodes.new("ShaderNodeVectorMath")
    view_neg.location = (-1000, -350)
    view_neg.operation = "MULTIPLY"
    view_neg.inputs[1].default_value = (-6.0, -6.0, 0.0)

    sep_view = nodes.new("ShaderNodeSeparateXYZ")
    sep_view.location = (-800, -350)

    sep_obj = nodes.new("ShaderNodeSeparateXYZ")
    sep_obj.location = (-800, -500)

    dist_tex = nodes.new("ShaderNodeTexImage")
    dist_tex.location = (-800, -650)
    dist_tex.image = dist_img
    dist_tex.extension = "REPEAT"

    sep_dist = nodes.new("ShaderNodeSeparateColor")
    sep_dist.location = (-600, -650)
    sep_dist.mode = "RGB"

    add_x = nodes.new("ShaderNodeMath")
    add_x.location = (-600, -350)
    add_x.operation = "ADD"

    add_y = nodes.new("ShaderNodeMath")
    add_y.location = (-600, -450)
    add_y.operation = "ADD"

    foil_x = nodes.new("ShaderNodeMath")
    foil_x.location = (-400, -350)
    foil_x.operation = "ADD"

    foil_y = nodes.new("ShaderNodeMath")
    foil_y.location = (-400, -450)
    foil_y.operation = "ADD"

    dist_x = nodes.new("ShaderNodeMath")
    dist_x.location = (-600, -530)
    dist_x.operation = "MULTIPLY"
    dist_x.inputs[1].default_value = 0.25

    dist_y = nodes.new("ShaderNodeMath")
    dist_y.location = (-600, -610)
    dist_y.operation = "MULTIPLY"
    dist_y.inputs[1].default_value = 0.25

    combine_uv = nodes.new("ShaderNodeCombineXYZ")
    combine_uv.location = (-200, -400)

    rainbow_tex = nodes.new("ShaderNodeTexImage")
    rainbow_tex.location = (0, -400)
    rainbow_tex.image = rainbow_img
    rainbow_tex.extension = "REPEAT"

    cosmos_tex = nodes.new("ShaderNodeTexImage")
    cosmos_tex.location = (-750, 80)
    cosmos_tex.image = cosmos_img
    cosmos_tex.interpolation = "Linear"

    foil_mix = nodes.new("ShaderNodeMix")
    foil_mix.location = (100, -250)
    foil_mix.data_type = "RGBA"
    foil_mix.blend_type = "SCREEN"
    foil_mix.inputs["Factor"].default_value = 0.65

    holo_screen = nodes.new("ShaderNodeMix")
    holo_screen.location = (200, 100)
    holo_screen.data_type = "RGBA"
    holo_screen.blend_type = "SCREEN"
    holo_screen.inputs["Factor"].default_value = 0.75

    sep_uv = nodes.new("ShaderNodeSeparateXYZ")
    sep_uv.location = (-750, 500)

    mask_x = nodes.new("ShaderNodeMapRange")
    mask_x.location = (-550, 600)
    mask_x.clamp = True
    mask_x.inputs["From Min"].default_value = HOLO_UV_X_MIN
    mask_x.inputs["From Max"].default_value = HOLO_UV_X_MAX

    mask_y = nodes.new("ShaderNodeMapRange")
    mask_y.location = (-550, 450)
    mask_y.clamp = True
    mask_y.inputs["From Min"].default_value = HOLO_UV_Y_MIN
    mask_y.inputs["From Max"].default_value = HOLO_UV_Y_MAX

    mask_mul = nodes.new("ShaderNodeMath")
    mask_mul.location = (-350, 520)
    mask_mul.operation = "MULTIPLY"

    holo_mask = nodes.new("ShaderNodeMath")
    holo_mask.location = (-150, 520)
    holo_mask.operation = "ADD"
    holo_mask.inputs[1].default_value = 0.08
    holo_mask.use_clamp = True

    fresnel_mask = nodes.new("ShaderNodeMath")
    fresnel_mask.location = (0, 300)
    fresnel_mask.operation = "MULTIPLY"

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (400, 100)
    emission.inputs["Strength"].default_value = 0.6

    add_shader = nodes.new("ShaderNodeAddShader")
    add_shader.location = (650, 200)

    links.new(tex_coord.outputs["UV"], face_tex.inputs["Vector"])
    links.new(tex_coord.outputs["UV"], cosmos_tex.inputs["Vector"])
    links.new(tex_coord.outputs["UV"], sep_uv.inputs["Vector"])
    links.new(face_tex.outputs["Color"], principled.inputs["Base Color"])
    links.new(face_tex.outputs["Color"], holo_screen.inputs["B"])

    links.new(sep_uv.outputs["X"], mask_x.inputs["Value"])
    links.new(sep_uv.outputs["Y"], mask_y.inputs["Value"])
    links.new(mask_x.outputs["Result"], mask_mul.inputs[0])
    links.new(mask_y.outputs["Result"], mask_mul.inputs[1])
    links.new(mask_mul.outputs["Value"], holo_mask.inputs[0])

    links.new(geom.outputs["Incoming"], view_neg.inputs[0])
    links.new(view_neg.outputs["Vector"], sep_view.inputs["Vector"])
    links.new(tex_coord.outputs["Object"], sep_obj.inputs["Vector"])
    links.new(tex_coord.outputs["Object"], dist_tex.inputs["Vector"])

    links.new(sep_view.outputs["X"], add_x.inputs[0])
    links.new(sep_obj.outputs["X"], add_x.inputs[1])
    links.new(sep_view.outputs["Y"], add_y.inputs[0])
    links.new(sep_obj.outputs["Y"], add_y.inputs[1])

    links.new(dist_tex.outputs["Color"], sep_dist.inputs["Color"])
    links.new(sep_dist.outputs["Red"], dist_x.inputs[0])
    links.new(sep_dist.outputs["Green"], dist_y.inputs[0])
    links.new(add_x.outputs["Value"], foil_x.inputs[0])
    links.new(dist_x.outputs["Value"], foil_x.inputs[1])
    links.new(add_y.outputs["Value"], foil_y.inputs[0])
    links.new(dist_y.outputs["Value"], foil_y.inputs[1])

    links.new(foil_x.outputs["Value"], combine_uv.inputs["X"])
    links.new(foil_y.outputs["Value"], combine_uv.inputs["Y"])
    links.new(combine_uv.outputs["Vector"], rainbow_tex.inputs["Vector"])
    links.new(cosmos_tex.outputs["Color"], foil_mix.inputs["A"])
    links.new(rainbow_tex.outputs["Color"], foil_mix.inputs["B"])
    links.new(foil_mix.outputs["Result"], holo_screen.inputs["A"])
    links.new(layer.outputs["Fresnel"], holo_screen.inputs["Factor"])

    links.new(layer.outputs["Fresnel"], fresnel_mask.inputs[0])
    links.new(holo_mask.outputs["Value"], fresnel_mask.inputs[1])
    links.new(holo_screen.outputs["Result"], emission.inputs["Color"])
    links.new(fresnel_mask.outputs["Value"], emission.inputs["Strength"])

    links.new(principled.outputs["BSDF"], add_shader.inputs[0])
    links.new(emission.outputs["Emission"], add_shader.inputs[1])
    links.new(add_shader.outputs["Shader"], output.inputs["Surface"])
    return mat


def create_back_material(back_img):
    if back_img.pixels[0] == 0.0:
        back_img.reload()

    mat = bpy.data.materials.new("CardBack")
    mat.use_nodes = True
    mat.use_backface_culling = True
    mat.diffuse_color = (0.12, 0.22, 0.55, 1.0)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)

    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-400, 0)

    back_tex = nodes.new("ShaderNodeTexImage")
    back_tex.location = (-150, 0)
    back_tex.image = back_img
    back_tex.interpolation = "Linear"

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (100, 0)
    principled.inputs["Roughness"].default_value = 0.38
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = 0.35

    links.new(tex_coord.outputs["UV"], back_tex.inputs["Vector"])
    links.new(back_tex.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return mat


def create_edge_material():
    mat = bpy.data.materials.new("CardEdge")
    mat.use_nodes = True
    mat.use_backface_culling = True
    mat.diffuse_color = (0.06, 0.1, 0.24, 1.0)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (0.06, 0.1, 0.24, 1.0)
    principled.inputs["Roughness"].default_value = 0.55
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def rounded_rect_points(half_w, half_h, radius, segments):
    """CCW outline of a rounded rectangle centered on the origin."""
    r = min(radius, half_w - 1e-6, half_h - 1e-6)
    corners = (
        (-half_w + r, -half_h + r, math.pi, 1.5 * math.pi),
        (half_w - r, -half_h + r, 1.5 * math.pi, 2.0 * math.pi),
        (half_w - r, half_h - r, 0.0, 0.5 * math.pi),
        (-half_w + r, half_h - r, 0.5 * math.pi, math.pi),
    )
    points = []
    for cx, cy, angle_start, angle_end in corners:
        for i in range(segments):
            angle = angle_start + (angle_end - angle_start) * (i / segments)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def assign_card_uvs(mesh, half_w=None, half_h=None):
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv_layer = mesh.uv_layers.active.data
    verts = mesh.vertices
    if half_w is not None and half_h is not None:
        min_x, max_x = -half_w, half_w
        min_y, max_y = -half_h, half_h
    else:
        min_x = min(v.co.x for v in verts)
        max_x = max(v.co.x for v in verts)
        min_y = min(v.co.y for v in verts)
        max_y = max(v.co.y for v in verts)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    for poly in mesh.polygons:
        flip_u = poly.normal.z < -0.5
        for loop_index in poly.loop_indices:
            co = verts[mesh.loops[loop_index].vertex_index].co
            u = (co.x - min_x) / span_x
            v = (co.y - min_y) / span_y
            if flip_u:
                u = 1.0 - u
            uv_layer[loop_index].uv = (u, v)


def create_card_mesh(front_material, back_material, edge_material):
    half_w = CARD_WIDTH / 2
    half_h = CARD_HEIGHT / 2
    half_t = CARD_THICKNESS / 2

    bm = bmesh.new()
    outline = rounded_rect_points(
        half_w, half_h, CARD_CORNER_RADIUS, CARD_CORNER_SEGMENTS
    )
    top_verts = [bm.verts.new((x, y, half_t)) for x, y in outline]
    bottom_verts = [bm.verts.new((x, y, -half_t)) for x, y in outline]
    bm.verts.ensure_lookup_table()

    bm.faces.new(top_verts)
    bm.faces.new(list(reversed(bottom_verts)))
    vert_count = len(outline)
    for i in range(vert_count):
        j = (i + 1) % vert_count
        bm.faces.new([top_verts[i], top_verts[j], bottom_verts[j], bottom_verts[i]])

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new("HoloCharizardCardMesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    assign_card_uvs(mesh, half_w, half_h)

    for poly in mesh.polygons:
        if poly.normal.z > 0.5:
            poly.material_index = 0  # front (Charizard)
        elif poly.normal.z < -0.5:
            poly.material_index = 1  # back (Pokéball)
        else:
            poly.material_index = 2

    card = bpy.data.objects.new("HoloCharizardCard", mesh)
    bpy.context.collection.objects.link(card)
    bpy.context.view_layer.objects.active = card
    card.select_set(True)

    bevel = card.modifiers.new("Bevel", "BEVEL")
    bevel.width = min(CARD_CORNER_RADIUS * 0.12, CARD_THICKNESS * 0.45)
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(35)

    card.data.materials.append(front_material)
    card.data.materials.append(back_material)
    card.data.materials.append(edge_material)
    return card


# ---------------------------------------------------------------------------
# Scene, lighting, render settings
# ---------------------------------------------------------------------------
def point_camera_at(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene(card):
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False

    if hasattr(scene, "eevee"):
        eevee = scene.eevee
        if hasattr(eevee, "use_bloom"):
            eevee.use_bloom = True
        if hasattr(eevee, "bloom_intensity"):
            eevee.bloom_intensity = 0.04
        if hasattr(eevee, "bloom_threshold"):
            eevee.bloom_threshold = 0.85

    world = bpy.data.worlds.new("StudioWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()
    wout = wn.new("ShaderNodeOutputWorld")
    wbg = wn.new("ShaderNodeBackground")
    wbg.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1.0)
    wbg.inputs["Strength"].default_value = 0.4
    wl.new(wbg.outputs["Background"], wout.inputs["Surface"])

    # Table
    bpy.ops.mesh.primitive_plane_add(size=50.0, location=(0, 0, 0))
    table = bpy.context.active_object
    table.name = "Table"
    table_mat = bpy.data.materials.new("TableMat")
    table_mat.use_nodes = True
    bsdf = table_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.06, 0.06, 0.07, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.65
    table.data.materials.append(table_mat)

    # Camera — baked rotation so camera view works immediately on file open
    bpy.ops.object.camera_add(location=(0.0, -12.0, 8.0))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.data.lens = 65
    cam.data.clip_start = 0.01
    cam.data.clip_end = 500.0
    bpy.context.scene.camera = cam

    def add_area(name, loc, energy, size, color):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.active_object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        light.data.color = color
        return light

    bpy.ops.object.light_add(type="SUN", location=(2.0, -3.0, 10.0))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 4.0
    sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(20))

    key = add_area("KeyLight", (8.0, -8.0, 14.0), 800, 12.0, (1.0, 0.97, 0.92))
    key.rotation_euler = (math.radians(55), math.radians(10), math.radians(25))

    rim = add_area("RimLight", (-10.0, 6.0, 10.0), 500, 8.0, (0.7, 0.85, 1.0))
    rim.rotation_euler = (math.radians(60), math.radians(-30), math.radians(-160))

    # Stand the card upright, facing the camera (normal toward -Y)
    lean = math.radians(CARD_LEAN_DEG)
    card.rotation_euler = (math.radians(90) - lean, 0, math.radians(-5))
    card.location = (0, 0, CARD_HEIGHT / 2)
    point_camera_at(cam, Vector((0, 0, CARD_HEIGHT * 0.55)))


def add_helper_scripts():
    on_open_path = os.path.join(PROJECT_ROOT, "scripts", "on_open.py")
    if os.path.isfile(on_open_path):
        text = bpy.data.texts.get("on_open")
        if text is None:
            text = bpy.data.texts.new("on_open")
        with open(on_open_path, encoding="utf-8") as handle:
            text.from_string(handle.read())


def configure_workspaces():
    """Persist Material Preview + camera view so the card isn't a flat yellow plane on open."""
    scene = bpy.context.scene
    cam = bpy.data.objects.get("Camera")
    if cam:
        scene.camera = cam
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                space.shading.type = "MATERIAL"
                space.shading.use_scene_lights = True
                space.shading.use_scene_world = True
                if screen.name == "Layout" and space.region_3d is not None:
                    space.region_3d.view_perspective = "CAMERA"


def add_frame_view_script():
    """Embedded script — run once from Scripting tab if the viewport is empty."""
    code = """import bpy


def frame_card():
    card = bpy.data.objects.get("HoloCharizardCard")
    cam = bpy.data.objects.get("Camera")
    if card is None:
        return
    bpy.ops.object.select_all(action="DESELECT")
    card.select_set(True)
    bpy.context.view_layer.objects.active = card
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region is None:
                continue
            override = bpy.context.temp_override(window=window, area=area, region=region)
            with override:
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True
                bpy.ops.view3d.view_selected()


frame_card()
"""
    text = bpy.data.texts.get("frame_card_view")
    if text is None:
        text = bpy.data.texts.new("frame_card_view")
    text.from_string(code)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ensure_dir(ASSETS_DIR)
    clear_scene()

    generate_texture_files()
    rainbow = load_image("Holo_Rainbow", "sRGB")
    distortion = load_image("Holo_Distortion", "Non-Color")
    face = load_image("Charizard_Base_Set", "sRGB")
    cosmos = load_image("Cosmos_Holo", "sRGB")
    back = load_image("Card_Back", "sRGB")

    front_material = create_card_material(rainbow, distortion, face, cosmos)
    back_material = create_back_material(back)
    edge_material = create_edge_material()
    card = create_card_mesh(front_material, back_material, edge_material)
    setup_scene(card)
    configure_workspaces()
    add_helper_scripts()
    add_frame_view_script()

    # Annotations for the user
    card["texture_note"] = (
        "Front: Charizard_Base_Set.jpg. Back: Card_Back.png (Pokemon TCG API). "
        "Cosmos foil: Cosmos_Holo.png."
    )

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"\n✓ Saved: {BLEND_PATH}")
    print("  Open in Blender and orbit the camera (View → Cameras → Active Camera, then Numpad 0)")
    print("  Viewport should open in Material Preview (camera view). If solid yellow, click the 3rd sphere icon.")


if __name__ == "__main__":
    main()