bl_info = {
    "name": "Workers & Resources Renderconfig Exporter",
    "author": "Lex713",
    "version": (1, 3),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > WRSR",
    "description": "Automates creation of renderconfig file for Workers & Resources: Soviet Republic",
    "category": "Import-Export",
}

import bpy
from bpy.props import (
    StringProperty, BoolProperty, FloatProperty, IntProperty,
    PointerProperty, CollectionProperty
)
from bpy_extras.io_utils import ExportHelper

# ---------------------------
# Properties (user input)
# ---------------------------

class DebrisMesh(bpy.types.PropertyGroup):
    nmf: StringProperty(name="Mesh NMF", default="buildings/buildingwreck1.nmf")
    mtl: StringProperty(name="Mesh MTL", default="buildings/buildingwreck.mtl")


class GameINIProperties(bpy.types.PropertyGroup):
    # Core fields
    model_name: StringProperty(name="Model", default="model.nmf")
    lod_model_name: StringProperty(name="LOD Model", default="")
    lod_distance: bpy.props.FloatProperty(
        name="LOD Distance",
        default=700.0,            # sensible default
        description="Distance at which LOD model will swap in")
    material_name: StringProperty(name="Material", default="material.mtl")
    emissive_material: StringProperty(name="Emissive Material", default="")
    # Toggles
    enable_planeshadow: BoolProperty(name="PLANESHADOW", default=False)
    enable_reflection: BoolProperty(name="REFLECTION", default=False)
    use_destruction: bpy.props.BoolProperty(name="Destruction Visualization", default=False)
    # Destruction defaults
    life: bpy.props.FloatProperty(name="Life", default=3800.0)
    derbis_num: bpy.props.IntProperty(name="Derbis Num", default=15)
    derbis_scale: bpy.props.FloatProperty(name="Derbis Scale", default=1.4)


# ---------------------------
# Helpers / Light creation
# ---------------------------

def add_light(name, light_type="POINT", color=(1, 1, 1), radius=1.0, energy=1000.0):
    light_data = bpy.data.lights.new(name=name, type=light_type)
    light_data.color = color
    light_data.shadow_soft_size = radius
    light_data.energy = energy
    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.collection.objects.link(light_obj)
    bpy.context.view_layer.objects.active = light_obj
    light_obj.select_set(True)
    return light_obj


class OT_AddLight(bpy.types.Operator):
    bl_idname = "object.add_light_token"
    bl_label = "Add LIGHT"
    def execute(self, context):
        add_light("LIGHT", "POINT", (1, 1, 1), 1.0, 1000.0)
        return {'FINISHED'}


class OT_AddRGBLight(bpy.types.Operator):
    bl_idname = "object.add_rgb_light_token"
    bl_label = "Add LIGHT_RGB"
    def execute(self, context):
        add_light("LIGHT_RGB", "POINT", (1, 0, 0), 1.0, 1000.0)
        return {'FINISHED'}


class OT_AddRGBBlinkLight(bpy.types.Operator):
    bl_idname = "object.add_rgb_blick_light_token"
    bl_label = "Add LIGHT_RGB_BLICK"
    def execute(self, context):
        add_light("LIGHT_RGB_BLICK", "POINT", (0, 1, 0), 1.0, 1000.0)
        return {'FINISHED'}


# ---------------------------
# Export Operator
# ---------------------------

class OT_ExportINI(bpy.types.Operator, ExportHelper):
    """Export scene to custom INI"""
    bl_idname = "export_scene.custom_ini"
    bl_label = "Export INI"
    filename_ext = ".ini"
    filter_glob: StringProperty(default="*.ini", options={'HIDDEN'})

    def execute(self, context):
        props = context.scene.game_ini_props
        lines = []
        lines.append("$TYPE_WORKSHOP")

        # Required & optional headers
        if props.model_name: lines.append(f"MODEL {props.model_name}")
        if props.lod_model_name:
            lines.append(f"MODEL_LOD {props.lod_model_name} {props.lod_distance:.1f}")
        if props.material_name: lines.append(f"MATERIAL {props.material_name}")
        if props.emissive_material: lines.append(f"MATERIALEMISSIVE {props.emissive_material}")
        if props.enable_planeshadow: lines.append("PLANESHADOW")
        if props.enable_reflection: lines.append("REFLECTION")

        # Destruction stuff
        if props.use_destruction:
            lines.append(f"LIFE {props.life}")
            lines.append("DERBIS_FALLING_FX buildingfall1 1.000000")
            lines.append("DERBIS_FALLED_FX buildingfall2 1.400000")
            lines.append("DERBIS_FALLED_SFX collapse")
            lines.append(f"DERBIS_NUM {props.derbis_num}")
            lines.append("DERBIS_FALLING_FX_MAXTIME 3.000000")
            lines.append(f"DERBIS_SCALE {props.derbis_scale}")
            lines.append("DERBIS_MESH buildings/buildingwreck1.nmf buildings/buildingwreck.mtl")
            lines.append("DERBIS_MESH buildings/buildingwreck2.nmf buildings/buildingwreck.mtl")
            lines.append("DERBIS_MESH buildings/buildingwreck3.nmf buildings/buildingwreck.mtl")
            
        # Lights (export X Z Y, V from radius)
        for obj in bpy.context.scene.objects:
            if obj.type == "LIGHT":
                lx, ly, lz = obj.location.x, obj.location.y, obj.location.z
                v = getattr(obj.data, "shadow_soft_size", 1.0)
                r, g, b = obj.data.color[:]
                if obj.name.startswith("LIGHT_RGB_BLICK"):
                    lines.append(f"LIGHT_RGB_BLICK {lx:.3f} {lz:.3f} {ly:.3f} {v:.3f} {r:.3f} {g:.3f} {b:.3f}")
                elif obj.name.startswith("LIGHT_RGB"):
                    lines.append(f"LIGHT_RGB {lx:.3f} {lz:.3f} {ly:.3f} {v:.3f} {r:.3f} {g:.3f} {b:.3f}")
                elif obj.name.startswith("LIGHT"):
                    lines.append(f"LIGHT {lx:.3f} {lz:.3f} {ly:.3f} {v:.3f}")

        lines.append("END")

        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        self.report({'INFO'}, f"INI exported to {self.filepath}")
        return {'FINISHED'}
        

# ---------------------------
# UI Panel
# ---------------------------

class VIEW3D_PT_GameTools(bpy.types.Panel):
    bl_label = "Renderconfig Editor"
    bl_idname = "VIEW3D_PT_game_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "WRSR"

    def draw(self, context):
        layout = self.layout
        props = context.scene.game_ini_props

        # Core
        layout.label(text="File Settings:")
        layout.prop(props, "model_name")
        layout.prop(props, "lod_model_name")
        layout.prop(props, "lod_distance")
        layout.prop(props, "material_name")
        layout.prop(props, "emissive_material")

        layout.separator()
        layout.label(text="Flags:")
        row = layout.row(align=True)
        row.prop(props, "enable_planeshadow")
        row.prop(props, "enable_reflection")

        layout.separator()
        layout.prop(props, "use_destruction")
        if props.use_destruction:
            box = layout.box()
            box.prop(props, "life")
            box.prop(props, "derbis_num")
            box.prop(props, "derbis_scale")

        layout.separator()
        layout.label(text="Add Lights:")
        layout.operator("object.add_light_token")
        layout.operator("object.add_rgb_light_token")
        layout.operator("object.add_rgb_blick_light_token")

        layout.separator()
        layout.label(text="Export:")
        layout.operator("export_scene.custom_ini")


# ---------------------------
# Registration
# ---------------------------

classes = (
    DebrisMesh,
    GameINIProperties,
    OT_AddLight,
    OT_AddRGBLight,
    OT_AddRGBBlinkLight,
    OT_ExportINI,
    VIEW3D_PT_GameTools,
)

def register():
    bpy.utils.register_class(GameINIProperties)
    bpy.utils.register_class(OT_ExportINI)
    bpy.utils.register_class(VIEW3D_PT_GameTools)

    bpy.types.Scene.game_ini_props = bpy.props.PointerProperty(type=GameINIProperties)


def unregister():
    del bpy.types.Scene.game_ini_props
    bpy.utils.unregister_class(VIEW3D_PT_GameTools)
    bpy.utils.unregister_class(OT_ExportINI)
    bpy.utils.unregister_class(GameINIProperties)


if __name__ == "__main__":
    register()

