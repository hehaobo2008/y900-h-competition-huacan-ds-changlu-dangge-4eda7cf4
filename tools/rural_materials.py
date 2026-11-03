"""Reusable, glTF-compatible material nodes and UVs for the rural rebuild."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "assets" / "materials" / "polyhaven"

def pbr(name, asset, derived=False, roughness=0.9, normal_strength=0.45,
        vertex_color=False, diffuse_override=None, alpha=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    filename = diffuse_override or ("Diffuse_rural.jpg" if derived else "Diffuse.jpg")
    diffuse = bpy.data.images.load(str(LIB / asset / filename), check_existing=True)
    color = nodes.new("ShaderNodeTexImage")
    color.image = diffuse
    if vertex_color:
        attr = nodes.new("ShaderNodeVertexColor")
        attr.layer_name = "Col"
        mix = nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        links.new(color.outputs["Color"], mix.inputs[6])
        links.new(attr.outputs["Color"], mix.inputs[7])
        links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    else:
        links.new(color.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:
        mat.surface_render_method = "DITHERED"
        links.new(color.outputs["Alpha"], bsdf.inputs["Alpha"])
    normal_image = bpy.data.images.load(str(LIB / asset / "nor_gl.jpg"), check_existing=True)
    normal_image.colorspace_settings.name = "Non-Color"
    tex_normal = nodes.new("ShaderNodeTexImage")
    tex_normal.image = normal_image
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = normal_strength
    links.new(tex_normal.outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    rough_image = bpy.data.images.load(str(LIB / asset / "Rough.jpg"), check_existing=True)
    rough_image.colorspace_settings.name = "Non-Color"
    tex_rough = nodes.new("ShaderNodeTexImage")
    tex_rough.image = rough_image
    links.new(tex_rough.outputs["Color"], bsdf.inputs["Roughness"])
    return mat

def project_uv(obj, scale=0.6, grain_axis=None, offset=0.0, use_transform=False):
    """Per-face planar UV in local metres; grain_axis is the longest timber axis."""
    mesh = obj.data
    uv = mesh.uv_layers.active or mesh.uv_layers.new(name="UVMap")
    for face in mesh.polygons:
        n = face.normal
        dominant = max(range(3), key=lambda i: abs(n[i]))
        axes = [i for i in range(3) if i != dominant]
        if grain_axis in axes:
            # The wood image grain is vertical (V), so orient V along the member.
            axes.remove(grain_axis)
            uaxis, vaxis = axes[0], grain_axis
        else:
            uaxis, vaxis = axes
        for li in face.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index].co
            if use_transform:
                v = obj.matrix_world @ v
            uv.data[li].uv = (v[uaxis] / scale + offset, v[vaxis] / scale + offset * 0.37)
