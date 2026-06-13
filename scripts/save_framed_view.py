"""Open the blend file, switch to camera view, and save. Run without --background."""
import bpy


def save_framed(_=0):
    card = bpy.data.objects.get("HoloCharizardCard")
    cam = bpy.data.objects.get("Camera")
    if card is None or cam is None:
        return None

    bpy.context.scene.camera = cam
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

    bpy.ops.wm.save_mainfile()
    print("Saved with camera view framed.")
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(save_framed, first_interval=1.0)