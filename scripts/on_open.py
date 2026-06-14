"""Runs automatically when holo_charizard.blend opens (enable once in Preferences → Save & Load → Auto Run Python Scripts)."""
import bpy


def _reload_textures():
    for name in (
        "Charizard_Base_Set",
        "Card_Back",
        "Cosmos_Holo",
        "Cosmos_Holo_Middle",
        "Holo_Rainbow",
        "Holo_Distortion",
    ):
        img = bpy.data.images.get(name)
        if img and img.packed_file is None:
            img.reload()


def _set_material_preview():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"
                    space.shading.use_scene_lights = True
                    space.shading.use_scene_world = True


def _frame_card(_dummy):
    card = bpy.data.objects.get("HoloCharizardCard")
    if card is None:
        return
    _reload_textures()
    _set_material_preview()
    bpy.ops.object.select_all(action="DESELECT")
    card.select_set(True)
    bpy.context.view_layer.objects.active = card
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
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


if _frame_card not in bpy.app.handlers.load_post:
    bpy.app.handlers.load_post.append(_frame_card)