"""Build one character with MPFB and export it.

Run inside Blender:
    blender --background --factory-startup --python scripts/build_character.py -- characters/<id>.json

--factory-startup gives an empty, predictable scene; MPFB is enabled below.
Writes exports/<id>.glb and previews/<id>.png next to the characters folder.
"""

import json
import math
import os
import sys

import addon_utils
import bpy

MPFB = "bl_ext.blender_org.mpfb"
addon_utils.enable(MPFB, default_set=True)

from bl_ext.blender_org.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.blender_org.mpfb.services.locationservice import LocationService  # noqa: E402
from bl_ext.blender_org.mpfb.services.targetservice import TargetService  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = LocationService.get_user_data()


def log(*parts):
    print("[build]", *parts, flush=True)


def asset(kind, name, ext=".mhclo"):
    """Path of an installed asset file, e.g. asset("hair", "bob02")."""
    folder = os.path.join(DATA, kind, name)
    for f in os.listdir(folder):
        if f.endswith(ext):
            return os.path.join(folder, f)
    raise FileNotFoundError(f"No {ext} in {folder}")


def age_to_macro(years):
    # MakeHuman: 0.0 = 1 yr, 0.1875 = 11, 0.5 = 25, 1.0 = 90
    if years <= 25:
        return 0.1875 + (years - 11) / (25 - 11) * (0.5 - 0.1875)
    return 0.5 + (years - 25) / (90 - 25) * 0.5


def tint(obj, hex_colour):
    """Multiply the texture feeding each material's base colour by a colour (e.g. dark hair)."""
    rgb = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [c ** 2.2 for c in rgb]  # sRGB to linear
    for slot in obj.material_slots:
        tree = slot.material.node_tree
        for node in tree.nodes:
            if node.type != "BSDF_PRINCIPLED" or not node.inputs["Base Color"].links:
                continue
            link = node.inputs["Base Color"].links[0]
            mix = tree.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs["B"].default_value = (*rgb, 1)
            tree.links.new(link.from_socket, mix.inputs["A"])
            tree.links.new(mix.outputs["Result"], node.inputs["Base Color"])


def flat_colour(obj, hex_colour, roughness=None, subsurface=None):
    """Replace the texture on each material's base colour with one plain colour (smooth cartoon look)."""
    for slot in obj.material_slots:
        tree = slot.material.node_tree
        for node in tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            for link in list(node.inputs["Base Color"].links):
                tree.links.remove(link)
            node.inputs["Base Color"].default_value = linear(hex_colour)
            if roughness is not None:
                for link in list(node.inputs["Roughness"].links):
                    tree.links.remove(link)
                node.inputs["Roughness"].default_value = roughness
            if subsurface is not None and "Subsurface Weight" in node.inputs:
                node.inputs["Subsurface Weight"].default_value = subsurface


def linear(hex_colour):
    return [(int(hex_colour[i:i + 2], 16) / 255) ** 2.2 for i in (1, 3, 5)] + [1.0]


def set_eye_settings(eyes, cfg):
    """Iris size and colours on MPFB's procedural eye material."""
    values = {"IrisToEyeWhiteRelation": cfg.get("iris_size", 0.39)}
    if "iris" in cfg:
        values["IrisMajorColor"] = linear(cfg["iris"])
        values["IrisMinorColor"] = linear(cfg.get("iris_inner", cfg["iris"]))
        values["IrisSection4Color"] = linear(cfg.get("iris_ring", "#120A06"))
    for slot in eyes.material_slots:
        for node in slot.material.node_tree.nodes:
            for name, value in values.items():
                if name in node.inputs:
                    node.inputs[name].default_value = value


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def build(spec):
    eth = spec["ethnicity"]
    macro = TargetService.get_default_macro_info_dict()
    macro.update({
        "gender": 0.0 if spec["sex"] == "female" else 1.0,
        "age": age_to_macro(spec["age"]),
        "height": spec.get("height", 0.5),
        "weight": spec.get("build", 0.5),
        "cupsize": spec.get("bust", 0.5),
        "proportions": 0.6,
        "race": {"asian": eth.get("asian", 0), "caucasian": eth.get("european", 0),
                 "african": eth.get("african", 0)},
    })
    basemesh = HumanService.create_human(macro_detail_dict=macro)
    log("human created")

    for name, weight in spec.get("stylise", {}).get("targets", {}).items():
        TargetService.load_target(basemesh, TargetService.target_full_path(name), weight=min(weight, 1.0), name=name)
        if weight > 1.0:  # exaggerate past MPFB's normal range (cartoon proportions)
            key = basemesh.data.shape_keys.key_blocks[name]
            key.slider_max = weight
            key.value = weight
    log("stylise targets applied")

    HumanService.set_character_skin(asset("skins", spec["skin"], ".mhmat"), basemesh, skin_type="MAKESKIN")
    if "skin_colour" in spec:
        flat_colour(basemesh, spec["skin_colour"], roughness=0.55, subsurface=0.2)
    elif "skin_tint" in spec:
        tint(basemesh, spec["skin_tint"])
    eyes = HumanService.add_mhclo_asset(asset("eyes", "low-poly"), basemesh, asset_type="Eyes", material_type="PROCEDURAL_EYES")
    set_eye_settings(eyes, spec.get("eyes", {}))
    brows = HumanService.add_mhclo_asset(asset("eyebrows", spec["eyebrows"]), basemesh, asset_type="Eyebrows", material_type="MAKESKIN")
    if "brow_colour" in spec:
        tint(brows, spec["brow_colour"])
    HumanService.add_mhclo_asset(asset("eyelashes", "eyelashes01"), basemesh, asset_type="Eyelashes", material_type="MAKESKIN")
    HumanService.add_mhclo_asset(asset("teeth", "teeth_base"), basemesh, asset_type="Teeth", material_type="MAKESKIN")
    HumanService.add_mhclo_asset(asset("tongue", "tongue01"), basemesh, asset_type="Tongue", material_type="MAKESKIN")
    hair = HumanService.add_mhclo_asset(asset("hair", spec["hair"]["asset"]), basemesh, asset_type="Hair", material_type="MAKESKIN")
    if "colour" in spec["hair"]:
        tint(hair, spec["hair"]["colour"])
    for item in spec.get("clothes", []):
        if isinstance(item, str):
            item = {"asset": item}
        cloth = HumanService.add_mhclo_asset(asset("clothes", item["asset"]), basemesh, asset_type="Clothes", material_type="MAKESKIN")
        if "colour" in item:
            flat_colour(cloth, item["colour"], roughness=0.9)
    log("assets added")

    HumanService.add_builtin_rig(basemesh, "game_engine")
    log("rig added")
    return basemesh


def bake_shape_keys():
    """Fold MPFB's shape keys (body settings) into the meshes so modifiers can be applied on export."""
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj.data.shape_keys:
            bpy.context.view_layer.objects.active = obj
            for o in bpy.context.selected_objects:
                o.select_set(False)
            obj.select_set(True)
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)


def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", export_apply=True,
                              export_yup=True, export_animations=False)
    log("exported", path, f"{os.path.getsize(path) / 1e6:.1f} MB")


def render_preview(basemesh, path):
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    coords = [basemesh.evaluated_get(deps).matrix_world @ v.co for v in basemesh.evaluated_get(deps).data.vertices]
    top = max(c.z for c in coords)
    height = top - min(c.z for c in coords)
    frame_bottom = top - 0.30 * height  # head to just below the chest
    centre_z = (top + frame_bottom) / 2 + 0.01 * height
    frame_h = (top - frame_bottom) * 1.1

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = frame_h
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0, -3, centre_z)
    cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam

    target = bpy.data.objects.new("LightTarget", None)
    target.location = (0, 0, centre_z)
    scene.collection.objects.link(target)
    for name, loc, energy, size in (("Key", (-1.2, -2, centre_z + 0.6), 70, 2.0),
                                    ("Fill", (1.5, -2, centre_z), 25, 3.0),
                                    ("Rim", (0.5, 2, centre_z + 0.5), 40, 1.0)):
        light = bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = size
        obj = bpy.data.objects.new(name, light)
        obj.location = loc
        track = obj.constraints.new("TRACK_TO")
        track.target = target
        scene.collection.objects.link(obj)

    world = bpy.data.worlds.new("White")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = world

    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    cam_data.sensor_fit = "VERTICAL"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    flatten_on_white(path)
    log("preview", path)


def flatten_on_white(path):
    """Put the transparent render on a white background, like the reference portraits."""
    import numpy as np
    img = bpy.data.images.load(path)
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    alpha = px[:, 3:4]
    px[:, :3] = px[:, :3] * alpha + (1 - alpha)
    px[:, 3] = 1
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()


def main():
    spec_path = sys.argv[sys.argv.index("--") + 1]
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    clear_scene()
    basemesh = build(spec)
    render_preview(basemesh, os.path.join(ROOT, "previews", spec["id"] + ".png"))
    bake_shape_keys()
    export_glb(os.path.join(ROOT, "exports", spec["id"] + ".glb"))
    log("done")


main()
