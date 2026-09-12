#!/usr/bin/env python3
"""Export the measured-layout revision. See accuracy.md for unresolved dimensions."""

from __future__ import annotations

import argparse
import base64
import json
import math
import re
import struct
import subprocess
from pathlib import Path


CEILING_HEIGHT = 2.8


MATERIALS = {
    "rough_wall": {"color": [.64,.63,.60,1], "roughness": 1},
    "rough_floor": {"color": [.54,.54,.52,1], "roughness": 1},
    "screed": {"color": [.62,.61,.58,1], "roughness": 1},
    "wall_beige": {"color": [.86,.81,.72,1], "roughness": .95},
    "ceiling_white": {"color": [.96,.96,.94,1], "roughness": .95},
    "door_ivory": {"color": [.92,.90,.84,1], "roughness": .76},
    "stone_gray": {"color": [.57,.58,.57,1], "roughness": .85},
    "tile_grout": {"color": [.46,.47,.46,1], "roughness": .95},
    "tile_wood": {"color": [.69,.53,.36,1], "roughness": .8},
    "sofa_olive": {"color": [.42,.46,.33,1], "roughness": 1},
    "wall": {"color": [0.87, 0.84, 0.78, 1.0], "metallic": 0.0, "roughness": 0.9},
    "wall_inner": {"color": [0.94, 0.92, 0.88, 1.0], "metallic": 0.0, "roughness": 0.92},
    "wall_bedroom_blue": {"color": [0.36, 0.49, 0.54, 1.0], "metallic": 0.0, "roughness": 0.92},
    "bedroom_oak": {"color": [0.74, 0.55, 0.35, 1.0], "metallic": 0.0, "roughness": 0.76},
    "bedroom_oak_panel": {"color": [0.69, 0.50, 0.32, 1.0], "metallic": 0.0, "roughness": 0.8},
    "bedroom_navy": {"color": [0.075, 0.15, 0.25, 1.0], "metallic": 0.0, "roughness": 1.0},
    "bedroom_ivory": {"color": [0.95, 0.94, 0.89, 1.0], "metallic": 0.0, "roughness": 1.0},
    "bedroom_rug": {"color": [0.79, 0.76, 0.68, 1.0], "metallic": 0.0, "roughness": 1.0},
    "bedroom_rug_weave": {"color": [0.69, 0.66, 0.59, 1.0], "metallic": 0.0, "roughness": 1.0},
    "bedroom_brass": {"color": [0.72, 0.57, 0.33, 1.0], "metallic": 0.65, "roughness": 0.35},
    "bedroom_lamp": {"color": [1.0, 0.89, 0.65, 1.0], "metallic": 0.0, "roughness": 0.6},
    "wall_bluegray": {"color": [0.63, 0.72, 0.80, 1.0], "metallic": 0.0, "roughness": 0.92},
    "floor_pale_oak": {"color": [0.84, 0.75, 0.60, 1.0], "metallic": 0.0, "roughness": 0.88},
    "floor_walnut": {"color": [0.49, 0.37, 0.29, 1.0], "metallic": 0.0, "roughness": 0.88},
    "mirror": {"color": [0.68, 0.78, 0.80, 1.0], "metallic": 0.95, "roughness": 0.08},
    "oak": {"color": [0.66, 0.46, 0.28, 1.0], "metallic": 0.0, "roughness": 0.74},
    "oak_light": {"color": [0.79, 0.65, 0.47, 1.0], "metallic": 0.0, "roughness": 0.76},
    "floor_oak": {"color": [0.72, 0.58, 0.42, 1.0], "metallic": 0.0, "roughness": 0.88},
    "floor_tile": {"color": [0.64, 0.66, 0.65, 1.0], "metallic": 0.0, "roughness": 0.82},
    "rug": {"color": [0.46, 0.53, 0.50, 1.0], "metallic": 0.0, "roughness": 1.0},
    "fabric": {"color": [0.73, 0.71, 0.66, 1.0], "metallic": 0.0, "roughness": 1.0},
    "fabric_light": {"color": [0.89, 0.86, 0.80, 1.0], "metallic": 0.0, "roughness": 1.0},
    "fabric_blue": {"color": [0.31, 0.42, 0.46, 1.0], "metallic": 0.0, "roughness": 1.0},
    "curtain_linen": {"color": [0.76, 0.71, 0.63, 1.0], "metallic": 0.0, "roughness": 1.0},
    "curtain_sheer": {"color": [0.96, 0.95, 0.91, 0.22], "metallic": 0.0, "roughness": 1.0},
    "dark": {"color": [0.15, 0.16, 0.16, 1.0], "metallic": 0.08, "roughness": 0.5},
    "metal": {"color": [0.42, 0.44, 0.44, 1.0], "metallic": 0.7, "roughness": 0.35},
    "white": {"color": [0.93, 0.93, 0.90, 1.0], "metallic": 0.0, "roughness": 0.7},
    "ceramic": {"color": [0.96, 0.97, 0.95, 1.0], "metallic": 0.0, "roughness": 0.32},
    "glass": {"color": [0.48, 0.72, 0.82, 0.30], "metallic": 0.0, "roughness": 0.18},
    "green": {"color": [0.22, 0.42, 0.28, 1.0], "metallic": 0.0, "roughness": 0.95},
    "terracotta": {"color": [0.66, 0.31, 0.21, 1.0], "metallic": 0.0, "roughness": 0.9},
}

for _base in ('stone_gray','tile_wood','floor_pale_oak','floor_walnut','floor_oak'):
    for _i,_factor in enumerate((.97,1.0,1.025)):
        MATERIALS[_base+'_'+str(_i)]={**MATERIALS[_base],
            'color':[min(1,c*_factor) for c in MATERIALS[_base]['color'][:3]]+[1]}
for _spec in MATERIALS.values():
    _spec.setdefault('metallic',0)


ELEMENTS: list[dict] = []
_NAME_COUNTS: dict[str, int] = {}


def unique_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_") or "Element"
    _NAME_COUNTS[safe] = _NAME_COUNTS.get(safe, 0) + 1
    return f"{safe}_{_NAME_COUNTS[safe]:03d}"


def add_box(
    name: str,
    material: str,
    x: float,
    z: float,
    width: float,
    depth: float,
    height: float,
    *,
    base: float = 0.0,
    rotation: float = 0.0,
    category: str = "furniture",
) -> None:
    ELEMENTS.append(
        {
            "shape": "box",
            "name": unique_name(name),
            "category": category,
            "material": material,
            "position": [round(x, 4), round(base + height / 2, 4), round(z, 4)],
            "size": [round(width, 4), round(height, 4), round(depth, 4)],
            "rotation": round(rotation, 6),
        }
    )


def add_cylinder(
    name: str,
    material: str,
    x: float,
    z: float,
    diameter: float,
    height: float,
    *,
    base: float = 0.0,
    category: str = "furniture",
) -> None:
    ELEMENTS.append(
        {
            "shape": "cylinder",
            "name": unique_name(name),
            "category": category,
            "material": material,
            "position": [round(x, 4), round(base + height / 2, 4), round(z, 4)],
            "size": [round(diameter, 4), round(height, 4), round(diameter, 4)],
            "rotation": 0.0,
        }
    )


def add_sofa(name: str, x: float, z: float, width: float, depth: float, facing: str, material: str = "fabric") -> None:
    add_box(f"Furniture_{name}_base", material, x, z, width, depth, 0.28, base=0.12)
    add_box(f"Furniture_{name}_seat", "fabric_light", x, z - (0.07 if facing == "north" else -0.07), width - 0.18, depth - 0.24, 0.18, base=0.40)
    back_z = z + (depth / 2 - 0.11) * (1 if facing == "north" else -1)
    add_box(f"Furniture_{name}_back", material, x, back_z, width, 0.20, 0.72, base=0.30)
    add_box(f"Furniture_{name}_arm", material, x - width / 2 + 0.10, z, 0.20, depth, 0.46, base=0.23)
    add_box(f"Furniture_{name}_arm", material, x + width / 2 - 0.10, z, 0.20, depth, 0.46, base=0.23)


def add_chair(
    name: str,
    x: float,
    z: float,
    rotation: float = 0.0,
    material: str = "fabric_blue",
    width: float = 0.44,
    depth: float = 0.44,
) -> None:
    add_box(f"Furniture_{name}_seat", material, x, z, width, depth, 0.12, base=0.43, rotation=rotation)
    offset_x = math.sin(rotation) * (depth / 2 - 0.04)
    offset_z = math.cos(rotation) * (depth / 2 - 0.04)
    add_box(f"Furniture_{name}_back", material, x + offset_x, z + offset_z, width - 0.02, 0.09, 0.54, base=0.52, rotation=rotation)
    for local_x in (-width / 2 + 0.06, width / 2 - 0.06):
        for local_z in (-depth / 2 + 0.06, depth / 2 - 0.06):
            rotated_x = local_x * math.cos(rotation) + local_z * math.sin(rotation)
            rotated_z = -local_x * math.sin(rotation) + local_z * math.cos(rotation)
            add_box(f"Furniture_{name}_leg", "dark", x + rotated_x, z + rotated_z, 0.032, 0.032, 0.43)


def add_office_chair(name: str, x: float, z: float, plan_angle: float = 0.0) -> None:
    add_cylinder(f"Furniture_{name}_seat", "fabric_blue", x, z, 0.50, 0.13, base=0.44)
    add_cylinder(f"Furniture_{name}_stem", "dark", x, z, 0.07, 0.43, base=0.05)
    back_x = x - math.sin(plan_angle) * 0.23
    back_z = z + math.cos(plan_angle) * 0.23
    add_box(f"Furniture_{name}_back", "fabric_blue", back_x, back_z, 0.46, 0.10, 0.58, base=0.54, rotation=plan_angle)
    for index in range(5):
        ray = index * math.tau / 5
        add_box(
            f"Furniture_{name}_base",
            "dark",
            x + math.cos(ray) * 0.15,
            z + math.sin(ray) * 0.15,
            0.31,
            0.035,
            0.035,
            base=0.04,
            rotation=-ray,
        )


def add_round_table(name: str, x: float, z: float, diameter: float, height: float = 0.74, material: str = "oak_light") -> None:
    add_cylinder(f"Furniture_{name}_top", material, x, z, diameter, 0.08, base=height - 0.08)
    add_cylinder(f"Furniture_{name}_pedestal", "dark", x, z, 0.16, height - 0.08)
    add_cylinder(f"Furniture_{name}_foot", "dark", x, z, diameter * 0.48, 0.035)


def add_plant(name: str, x: float, z: float, scale: float = 1.0) -> None:
    add_cylinder(f"Furniture_{name}_pot", "terracotta", x, z, 0.34 * scale, 0.34 * scale)
    add_cylinder(f"Furniture_{name}_stem", "green", x, z, 0.07 * scale, 0.72 * scale, base=0.28 * scale)
    for angle in (0.0, 1.05, 2.1, 3.15, 4.2, 5.25):
        add_box(
            f"Furniture_{name}_leaf",
            "green",
            x + math.cos(angle) * 0.18 * scale,
            z + math.sin(angle) * 0.18 * scale,
            0.32 * scale,
            0.13 * scale,
            0.035 * scale,
            base=0.72 * scale + (0.05 if int(angle * 10) % 2 else 0.0),
            rotation=-angle,
        )


def add_window_horizontal(name: str, x0: float, x1: float, z: float, depth: float = 0.055) -> None:
    width = x1 - x0
    add_box(f"Window_{name}_glass", "glass", (x0 + x1) / 2, z, width, depth, 1.40, base=0.85, category="window")
    for x in (x0, (x0 + x1) / 2, x1):
        add_box(f"Window_{name}_frame", "metal", x, z, 0.045, depth + 0.02, 1.44, base=0.83, category="window")
    add_box(f"Window_{name}_frame", "metal", (x0 + x1) / 2, z, width, depth + 0.02, 0.045, base=0.83, category="window")
    add_box(f"Window_{name}_frame", "metal", (x0 + x1) / 2, z, width, depth + 0.02, 0.045, base=2.23, category="window")


def add_window_vertical(name: str, z0: float, z1: float, x: float, width: float = 0.055) -> None:
    depth = z1 - z0
    add_box(f"Window_{name}_glass", "glass", x, (z0 + z1) / 2, width, depth, 1.40, base=0.85, category="window")
    for z in (z0, (z0 + z1) / 2, z1):
        add_box(f"Window_{name}_frame", "metal", x, z, width + 0.02, 0.045, 1.44, base=0.83, category="window")
    add_box(f"Window_{name}_frame", "metal", x, (z0 + z1) / 2, width + 0.02, depth, 0.045, base=0.83, category="window")
    add_box(f"Window_{name}_frame", "metal", x, (z0 + z1) / 2, width + 0.02, depth, 0.045, base=2.23, category="window")


def add_door_leaf(name: str, material: str, hinge_x: float, hinge_z: float, width: float, plan_angle: float, height: float) -> None:
    """Add a door from an exact hinge; plan_angle is measured in the X/Z drawing plane."""
    end_x = hinge_x + math.cos(plan_angle) * width
    end_z = hinge_z + math.sin(plan_angle) * width
    add_box(
        f"Door_{name}",
        material,
        (hinge_x + end_x) / 2,
        (hinge_z + end_z) / 2,
        width,
        0.045,
        height,
        rotation=-plan_angle,
        category="door",
    )


def build_scene() -> None:
    import sys
    from measured_layout import build
    ELEMENTS.clear()
    _NAME_COUNTS.clear()
    build(sys.modules[__name__])
    from finishes import build as build_finishes
    build_finishes(sys.modules[__name__])
    from furniture_catalog import build as build_catalog
    build_catalog(sys.modules[__name__])
    from designer_revision import build as apply_designer_revision
    apply_designer_revision(sys.modules[__name__])
    from comfort_revision import build as build_comfort
    build_comfort(sys.modules[__name__])
    from door_trim import build as build_door_trim
    build_door_trim(sys.modules[__name__])
    from cabinet_details import build as build_cabinet_details
    build_cabinet_details(sys.modules[__name__])
    from render_style import build as build_render_style
    build_render_style(sys.modules[__name__])
    from bathroom_towel import build as build_bathroom_towel
    build_bathroom_towel(sys.modules[__name__])
    from bathroom_finish import build as build_bathroom_finish
    build_bathroom_finish(sys.modules[__name__])
    from scene_lighting import build as build_scene_lighting
    build_scene_lighting(sys.modules[__name__])
    from kitchen_detail import build as build_kitchen_detail
    build_kitchen_detail(sys.modules[__name__])
    from apartment_detail import build as build_apartment_detail
    build_apartment_detail(sys.modules[__name__])
    from cabinet_motion import build as build_cabinet_motion
    build_cabinet_motion(sys.modules[__name__])
    for e in ELEMENTS:e.pop('inspectId',None)
    build_catalog(sys.modules[__name__])


def resolved(element):
    from finishes import resolved as resolve
    return resolve(element)


def ceiling_geometry():
    # Single underside: visible from the room; open to the overhead viewer.
    return ([-.5,-.5,-.5,.5,-.5,-.5,.5,-.5,.5,-.5,-.5,.5],
            [0,-1,0]*4,[0,1,2,0,2,3])




def cube_geometry() -> tuple[list[float], list[float], list[int]]:
    faces = [
        ((0, 0, 1), ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5))),
        ((0, 0, -1), ((0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5))),
        ((-1, 0, 0), ((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5))),
        ((1, 0, 0), ((0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5))),
        ((0, 1, 0), ((-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5))),
        ((0, -1, 0), ((-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5))),
    ]
    positions: list[float] = []
    normals: list[float] = []
    indices: list[int] = []
    for normal, vertices in faces:
        start = len(positions) // 3
        for vertex in vertices:
            positions.extend(vertex)
            normals.extend(normal)
        indices.extend((start, start + 1, start + 2, start, start + 2, start + 3))
    return positions, normals, indices


def cylinder_geometry(segments: int = 24) -> tuple[list[float], list[float], list[int]]:
    positions: list[float] = []
    normals: list[float] = []
    indices: list[int] = []
    for i in range(segments):
        a0 = math.tau * i / segments
        a1 = math.tau * (i + 1) / segments
        start = len(positions) // 3
        for angle, y in ((a0, -0.5), (a1, -0.5), (a1, 0.5), (a0, 0.5)):
            c, s = math.cos(angle), math.sin(angle)
            positions.extend((0.5 * c, y, 0.5 * s))
            normals.extend((c, 0.0, s))
        indices.extend((start, start + 2, start + 1, start, start + 3, start + 2))

        top = len(positions) // 3
        positions.extend((0.0, 0.5, 0.0, 0.5 * math.cos(a0), 0.5, 0.5 * math.sin(a0), 0.5 * math.cos(a1), 0.5, 0.5 * math.sin(a1)))
        normals.extend((0.0, 1.0, 0.0) * 3)
        indices.extend((top, top + 2, top + 1))

        bottom = len(positions) // 3
        positions.extend((0.0, -0.5, 0.0, 0.5 * math.cos(a1), -0.5, 0.5 * math.sin(a1), 0.5 * math.cos(a0), -0.5, 0.5 * math.sin(a0)))
        normals.extend((0.0, -1.0, 0.0) * 3)
        indices.extend((bottom, bottom + 2, bottom + 1))
    return positions, normals, indices


def hexagon_geometry():
    outline = [(0,-.5),(.5,-.313),(.5,.307),(0,.5),(-.5,.307),(-.5,-.313)]
    positions, normals, indices = [], [], []
    def tri(vertices, normal):
        start = len(positions)//3
        for p in vertices:
            positions.extend(p); normals.extend(normal)
        indices.extend((start,start+1,start+2))
    for i,(x,z) in enumerate(outline):
        nx,nz = outline[(i+1)%6]
        dx,dz = nx-x,nz-z
        length=math.hypot(dx,dz)
        n=(dz/length,0,-dx/length)
        a,b,c,d=(x,-.5,z),(nx,-.5,nz),(nx,.5,nz),(x,.5,z)
        tri((a,c,b),n); tri((a,d,c),n)
        tri(((0,.5,0),d,c),(0,1,0))
        tri(((0,-.5,0),b,a),(0,-1,0))
    # Outline is clockwise in an X/Z plan; reverse cap winding for Y-up.
    for i in range(0,len(indices),12):
        indices[i+7],indices[i+8]=indices[i+8],indices[i+7]
        indices[i+10],indices[i+11]=indices[i+11],indices[i+10]
    return positions,normals,indices


def build_glb(path: Path) -> None:
    binary = bytearray()
    buffer_views: list[dict] = []
    accessors: list[dict] = []

    def append_blob(blob: bytes, target: int) -> int:
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        binary.extend(blob)
        view_index = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(blob), "target": target})
        return view_index

    def add_geometry(positions: list[float], normals: list[float], indices: list[int]) -> tuple[int, int, int]:
        pos_view = append_blob(struct.pack(f"<{len(positions)}f", *positions), 34962)
        normal_view = append_blob(struct.pack(f"<{len(normals)}f", *normals), 34962)
        index_view = append_blob(struct.pack(f"<{len(indices)}H", *indices), 34963)
        pos_accessor = len(accessors)
        xs, ys, zs = positions[0::3], positions[1::3], positions[2::3]
        accessors.append(
            {
                "bufferView": pos_view,
                "componentType": 5126,
                "count": len(positions) // 3,
                "type": "VEC3",
                "min": [min(xs), min(ys), min(zs)],
                "max": [max(xs), max(ys), max(zs)],
            }
        )
        normal_accessor = len(accessors)
        accessors.append({"bufferView": normal_view, "componentType": 5126, "count": len(normals) // 3, "type": "VEC3"})
        index_accessor = len(accessors)
        accessors.append({"bufferView": index_view, "componentType": 5123, "count": len(indices), "type": "SCALAR"})
        return pos_accessor, normal_accessor, index_accessor

    cube_accessors = add_geometry(*cube_geometry())
    cylinder_accessors = add_geometry(*cylinder_geometry())
    hexagon_accessors = add_geometry(*hexagon_geometry())
    ceiling_accessors = add_geometry(*ceiling_geometry())

    material_names = list(MATERIALS)
    gltf_materials = []
    for material_name in material_names:
        spec = MATERIALS[material_name]
        alpha = spec["color"][3]
        material = {
            "name": material_name,
            "pbrMetallicRoughness": {
                "baseColorFactor": spec["color"],
                "metallicFactor": spec["metallic"],
                "roughnessFactor": spec["roughness"],
            },
            "doubleSided": alpha < 1.0,
        }
        if alpha < 1.0:
            material["alphaMode"] = "BLEND"
        if spec.get('pattern')==4:
            material['emissiveFactor']=spec['color'][:3]
        gltf_materials.append(material)

    meshes: list[dict] = []
    mesh_map: dict[tuple[str, str], int] = {}
    for shape in ("box", "cylinder", "hexagon", "ceiling"):
        position_accessor, normal_accessor, index_accessor = {"box":cube_accessors,"cylinder":cylinder_accessors,"hexagon":hexagon_accessors,"ceiling":ceiling_accessors}[shape]
        for material_index, material_name in enumerate(material_names):
            mesh_index = len(meshes)
            mesh_map[(shape, material_name)] = mesh_index
            meshes.append(
                {
                    "name": f"{shape}_{material_name}",
                    "primitives": [
                        {
                            "attributes": {"POSITION": position_accessor, "NORMAL": normal_accessor},
                            "indices": index_accessor,
                            "material": material_index,
                        }
                    ],
                }
            )

    nodes: list[dict] = [{"name": "Apartment", "children": list(range(1, len(ELEMENTS) + 1)), "extras": {"ceilingHeight": CEILING_HEIGHT, "units": "metres", "revision": "2026-09-08-measured", "accuracy": "Dimensioned anchors plus schematic tracing; see accuracy.md"}}]
    from detail_geometry import mesh as detail_mesh
    detail_map={}
    for element in ELEMENTS:
        element = resolved(element)
        mesh_index=mesh_map[(element['shape'],element['material'])]
        if element.get('detail'):
            key=json.dumps([element['detail'],element['size'],element['material']],sort_keys=True)
            if key not in detail_map:
                pa,na,ia=add_geometry(*detail_mesh(element))
                detail_map[key]=len(meshes)
                meshes.append(dict(name=element['name']+'_detailed',primitives=[dict(attributes={'POSITION':pa,'NORMAL':na},indices=ia,material=material_names.index(element['material']))]))
            mesh_index=detail_map[key]
        angle = element["rotation"]
        node = {
            "name": element["name"],
            "mesh": mesh_index,
            "translation": element["position"],
            "scale": element["size"],
            "extras": {"category": element["category"], "material": element["material"]},
        }
        if angle:
            node["rotation"] = [0.0, math.sin(angle / 2), 0.0, math.cos(angle / 2)]
        nodes.append(node)

    gltf = {
        "asset": {"version": "2.0", "generator": "Codex apartment-plan generator"},
        "scene": 0,
        "scenes": [{"name": "Apartment scene", "nodes": [0]}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": gltf_materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(binary)}],
    }

    json_bytes = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary)
    glb = bytearray(struct.pack("<III", 0x46546C67, 2, total_length))
    glb.extend(struct.pack("<I4s", len(json_bytes), b"JSON"))
    glb.extend(json_bytes)
    glb.extend(struct.pack("<I4s", len(binary), b"BIN\x00"))
    glb.extend(binary)
    path.write_bytes(glb)


def usd_identifier(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return value if not value[:1].isdigit() else f"_{value}"


def build_usda(path: Path) -> None:
    lines = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "Apartment"',
        "    metersPerUnit = 1",
        '    upAxis = "Y"',
        ")",
        "",
        'def Xform "Apartment" (',
        '    kind = "assembly"',
        ")",
        "{",
        '    def Scope "Materials"',
        "    {",
    ]
    for material_name, spec in MATERIALS.items():
        ident = usd_identifier(material_name)
        r, g, b, a = spec["color"]
        lines.extend(
            [
                f'        def Material "{ident}"',
                "        {",
                f"            token outputs:surface.connect = </Apartment/Materials/{ident}/Preview.outputs:surface>",
                '            def Shader "Preview"',
                "            {",
                '                uniform token info:id = "UsdPreviewSurface"',
                f"                color3f inputs:diffuseColor = ({r:.5f}, {g:.5f}, {b:.5f})",
                f"                float inputs:metallic = {spec['metallic']:.5f}",
                f"                float inputs:roughness = {spec['roughness']:.5f}",
                f"                float inputs:opacity = {a:.5f}",
                f"                color3f inputs:emissiveColor = ({r if spec.get('pattern')==4 else 0:.5f}, {g if spec.get('pattern')==4 else 0:.5f}, {b if spec.get('pattern')==4 else 0:.5f})",
                "                token outputs:surface",
                "            }",
                "        }",
            ]
        )
    lines.extend(["    }", ""])

    for element in ELEMENTS:
        element = resolved(element)
        name = usd_identifier(element["name"])
        x, y, z = element["position"]
        sx, sy, sz = element["size"]
        degrees = math.degrees(element["rotation"])
        material = usd_identifier(element["material"])
        primitive = 'Mesh' if element.get('detail') else {"box":"Cube", "cylinder":"Cylinder", "hexagon":"Mesh", "ceiling":"Mesh"}[element["shape"]]
        lines.extend(
            [
                f'    def Xform "{name}"',
                "    {",
                f'        custom string category = "{element["category"]}"',
                f"        double3 xformOp:translate = ({x:.5f}, {y:.5f}, {z:.5f})",
                f"        float xformOp:rotateY = {degrees:.5f}",
                f"        double3 xformOp:scale = ({sx:.5f}, {sy:.5f}, {sz:.5f})",
                '        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateY", "xformOp:scale"]',
                f'        def {primitive} "Geom"',
                "        {",
            ]
        )
        if primitive == "Cube":
            lines.append("            double size = 1")
        elif primitive == "Cylinder":
            lines.extend(['            uniform token axis = "Y"', "            double height = 1", "            double radius = 0.5"])
        else:
            from detail_geometry import mesh as detail_mesh
            positions,normals,indices=detail_mesh(element) if element.get('detail') else ceiling_geometry() if element['shape']=='ceiling' else hexagon_geometry()
            triples=lambda values: ', '.join('('+', '.join(f'{v:.6f}' for v in values[i:i+3])+')' for i in range(0,len(values),3))
            lines.extend([
                '            uniform token subdivisionScheme = "none"',
                '            point3f[] points = ['+triples(positions)+']',
                '            normal3f[] normals = ['+triples(normals)+'] (interpolation = "vertex")',
                '            int[] faceVertexCounts = ['+', '.join(['3']*(len(indices)//3))+']',
                '            int[] faceVertexIndices = ['+', '.join(map(str,indices))+']',
            ])
        lines.extend([f"            rel material:binding = </Apartment/Materials/{material}>", "        }", "    }", ""])
    lines.append("}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def scene_data():
    ambient_path=Path(__file__).resolve().parent/'kitchen-ambient.json'
    return {
        "metadata": {
            "title": "Квартира — замеры и планировка Лены",
            "ceilingHeight": CEILING_HEIGHT,
            "units": "м",
            "revision": "2026-09-09-interactive-bath-cabinet",
            "horizontalScale": "размерные привязки + обводка схемы; см. accuracy.md",
            "finishes": FINISH_SETTINGS,
            "designerSource": "07-08 План расстановки мебели 4.pdf, листы 7–8",
            "accuracy": "Подписанные габариты мебели — по PDF. Неподписанные оси и толщины стен — предварительные.",
        },
        "materials": MATERIALS,
        "elements": ELEMENTS,
        "objects": FURNITURE_CATALOG,
        "lights": SCENE_LIGHTS,
        "cabinetMotion": CABINET_MOTION,
        "detailAmbient": json.loads(ambient_path.read_text()) if ambient_path.exists() else None,
        "bounds": {"min": [-1.36, -0.06, -.21], "max": [9.33, CEILING_HEIGHT, 9.92]},
    }


def write_viewer_data(path: Path) -> None:
    data = scene_data()
    path.write_text("window.APARTMENT_SCENE = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")


def build_inline_fragment(source_dir: Path, output_path: Path) -> None:
    shell = (source_dir / "inline-shell.html").read_text(encoding="utf-8")
    css = (source_dir / "viewer.css").read_text(encoding="utf-8")
    js = (source_dir / "viewer-core.js").read_text(encoding="utf-8")
    scene_json = json.dumps(
        scene_data(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    fragment = shell.replace("/*__VIEWER_CSS__*/", css).replace("/*__VIEWER_CORE__*/", js).replace("/*__SCENE_JSON__*/", scene_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(fragment, encoding="utf-8")


def validate_glb(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("GLB is too short")
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2 or total != len(data):
        raise ValueError("Invalid GLB header")
    json_length, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON":
        raise ValueError("Missing GLB JSON chunk")
    document = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    if not document.get("nodes") or not document.get("meshes"):
        raise ValueError("GLB scene is empty")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--inline", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    build_scene()
    glb_path = output / "apartment-model.glb"
    usda_path = output / "apartment-model.usda"
    usdz_path = output / "apartment-model.usdz"
    build_glb(glb_path)
    validate_glb(glb_path)
    build_usda(usda_path)
    write_viewer_data(output / "scene-data.js")
    (output / 'bathroom-tile-layout.json').write_text(json.dumps({
        'units':'m','jointMm':2,'note':'Раскладка модели, подрезки по предварительным чистовым граням; не карта заказа или монтажа.',
        'reference':TILE_REFERENCE,'pieces':TILE_LAYOUT},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    usdzip = Path("/usr/bin/usdzip")
    if usdzip.exists():
        usdzip_scratch = output / "(A Document Being Saved By usdzip)"
        if usdz_path.exists():
            usdz_path.unlink()
        subprocess.run([str(usdzip), str(usdz_path), usda_path.name], cwd=output, check=True)
        if usdzip_scratch.is_dir() and not any(usdzip_scratch.iterdir()):
            usdzip_scratch.rmdir()

    if args.inline:
        build_inline_fragment(Path(__file__).resolve().parent, args.inline.resolve())

    print(f"elements={len(ELEMENTS)}")
    print(f"glb={glb_path} ({glb_path.stat().st_size} bytes)")
    print(f"usda={usda_path} ({usda_path.stat().st_size} bytes)")
    if usdz_path.exists():
        print(f"usdz={usdz_path} ({usdz_path.stat().st_size} bytes)")
    if args.inline:
        print(f"inline={args.inline.resolve()} ({args.inline.resolve().stat().st_size} bytes)")


if __name__ == "__main__":
    main()
