"""Shared EEVEE render configuration for holo-charizard scripts."""

import bpy

RENDER_RESOLUTION_X = 1920
RENDER_RESOLUTION_Y = 1080

# Blender 5.x removed scene.eevee bloom; use compositor Glare (Bloom type) instead.
BLOOM_THRESHOLD = 0.72
BLOOM_STRENGTH = 0.08
BLOOM_SIZE = 0.5
COMPOSITOR_GROUP_NAME = "HoloCharizardCompositor"


def _find_glare_node(node_group):
    for node in node_group.nodes:
        if node.bl_idname == "CompositorNodeGlare":
            return node
    return None


def _ensure_compositor_bloom(scene):
    """Wire compositor Bloom glare — replaces removed EEVEE scene.eevee bloom in 5.x."""
    scene.render.use_compositing = True

    node_group = scene.compositing_node_group
    if node_group is None:
        node_group = bpy.data.node_groups.new(COMPOSITOR_GROUP_NAME, "CompositorNodeTree")
        scene.compositing_node_group = node_group

    nodes = node_group.nodes
    links = node_group.links

    render_layers = nodes.get("Render Layers")
    if render_layers is None:
        nodes.clear()
        render_layers = nodes.new("CompositorNodeRLayers")
        render_layers.name = "Render Layers"
        render_layers.location = (0, 0)

    glare = _find_glare_node(node_group)
    if glare is None:
        glare = nodes.new("CompositorNodeGlare")
        glare.location = (300, 0)
        links.new(render_layers.outputs["Image"], glare.inputs["Image"])

    group_output = nodes.get("Group Output")
    if group_output is None:
        group_output = nodes.new("NodeGroupOutput")
        group_output.name = "Group Output"
        group_output.location = (600, 0)
    if not any(link.to_node == group_output for link in links):
        links.new(glare.outputs["Image"], group_output.inputs[0])

    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Threshold"].default_value = BLOOM_THRESHOLD
    glare.inputs["Strength"].default_value = BLOOM_STRENGTH
    glare.inputs["Size"].default_value = BLOOM_SIZE


def configure_eevee_render(scene, *, enable_compositor_bloom=True, png_output=False):
    """Apply shared EEVEE render settings used by setup and capture scripts."""
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RENDER_RESOLUTION_X
    scene.render.resolution_y = RENDER_RESOLUTION_Y
    scene.render.film_transparent = False

    if png_output:
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"

    if enable_compositor_bloom:
        _ensure_compositor_bloom(scene)