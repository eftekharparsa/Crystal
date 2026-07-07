bl_info = {
    "name": "Crystal Procedural Generator",
    "author": "Jules",
    "version": (1, 0),
    "blender": (3, 3, 0),
    "location": "View3D > Sidebar > Crystal",
    "description": "Procedurally generates atomic lattices using Geometry Nodes",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
import math

# Classes will go here

def create_crystal_geometry_nodes():
    """Creates a procedural geometry nodes group for crystal generation."""
    group_name = "Crystal_Procedural_Generator"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    group = bpy.data.node_groups.new(name=group_name, type='GeometryNodeTree')

    # Inputs
    inp_sx = group.inputs.new('NodeSocketInt', "Supercell X")
    inp_sy = group.inputs.new('NodeSocketInt', "Supercell Y")
    inp_sz = group.inputs.new('NodeSocketInt', "Supercell Z")
    inp_la = group.inputs.new('NodeSocketFloat', "Lattice Constant A")
    inp_lc = group.inputs.new('NodeSocketFloat', "Lattice Constant C")
    inp_temp = group.inputs.new('NodeSocketFloat', "Temperature")
    inp_def = group.inputs.new('NodeSocketFloat', "Defect Concentration")
    inp_str = group.inputs.new('NodeSocketFloat', "Strain")
    inp_csys = group.inputs.new('NodeSocketInt', "Crystal System")

    inp_sx.default_value = 3
    inp_sy.default_value = 3
    inp_sz.default_value = 3
    inp_la.default_value = 0.5
    inp_lc.default_value = 0.8
    inp_temp.default_value = 0.0
    inp_def.default_value = 0.0
    inp_str.default_value = 0.0
    inp_csys.default_value = 0

    # Outputs
    group.outputs.new('NodeSocketGeometry', "Geometry")

    nodes = group.nodes
    links = group.links

    # Node setup
    group_in = nodes.new('NodeGroupInput')
    group_in.location = (-800, 0)

    group_out = nodes.new('NodeGroupOutput')
    group_out.location = (800, 0)

    # Create grid/lattice using Mesh Lines
    line_x = nodes.new('GeometryNodeMeshLine')
    line_x.location = (-600, 400)
    line_x.inputs["Offset"].default_value = (1.0, 0.0, 0.0)
    links.new(group_in.outputs["Supercell X"], line_x.inputs["Count"])

    inst_y = nodes.new('GeometryNodeInstanceOnPoints')
    inst_y.location = (-400, 400)
    line_y = nodes.new('GeometryNodeMeshLine')
    line_y.location = (-600, 200)
    line_y.inputs["Offset"].default_value = (0.0, 1.0, 0.0)
    links.new(group_in.outputs["Supercell Y"], line_y.inputs["Count"])

    links.new(line_x.outputs["Mesh"], inst_y.inputs["Points"])
    links.new(line_y.outputs["Mesh"], inst_y.inputs["Instance"])

    realize_1 = nodes.new('GeometryNodeRealizeInstances')
    realize_1.location = (-200, 400)
    links.new(inst_y.outputs["Instances"], realize_1.inputs["Geometry"])

    inst_z = nodes.new('GeometryNodeInstanceOnPoints')
    inst_z.location = (0, 400)
    line_z = nodes.new('GeometryNodeMeshLine')
    line_z.location = (-200, 200)
    line_z.inputs["Offset"].default_value = (0.0, 0.0, 1.0)
    links.new(group_in.outputs["Supercell Z"], line_z.inputs["Count"])

    links.new(realize_1.outputs["Geometry"], inst_z.inputs["Points"])
    links.new(line_z.outputs["Mesh"], inst_z.inputs["Instance"])

    realize_2 = nodes.new('GeometryNodeRealizeInstances')
    realize_2.location = (200, 400)
    links.new(inst_z.outputs["Instances"], realize_2.inputs["Geometry"])

    # --- Crystal System Specific Offsets/Duplications ---
    # We will duplicate the base lattice for BCC and FCC and offset them.
    # Base Lattice Points
    base_points = realize_2

    # BCC duplication
    bcc_offset = nodes.new('GeometryNodeTransform')
    bcc_offset.location = (200, 200)
    bcc_offset.inputs["Translation"].default_value = (0.5, 0.5, 0.5)
    links.new(base_points.outputs["Geometry"], bcc_offset.inputs["Geometry"])

    bcc_join = nodes.new('GeometryNodeJoinGeometry')
    bcc_join.location = (400, 250)
    links.new(base_points.outputs["Geometry"], bcc_join.inputs["Geometry"])
    links.new(bcc_offset.outputs["Geometry"], bcc_join.inputs["Geometry"])

    # FCC duplication
    fcc_offset1 = nodes.new('GeometryNodeTransform')
    fcc_offset1.location = (200, 50)
    fcc_offset1.inputs["Translation"].default_value = (0.5, 0.5, 0.0)
    links.new(base_points.outputs["Geometry"], fcc_offset1.inputs["Geometry"])

    fcc_offset2 = nodes.new('GeometryNodeTransform')
    fcc_offset2.location = (200, -50)
    fcc_offset2.inputs["Translation"].default_value = (0.5, 0.0, 0.5)
    links.new(base_points.outputs["Geometry"], fcc_offset2.inputs["Geometry"])

    fcc_offset3 = nodes.new('GeometryNodeTransform')
    fcc_offset3.location = (200, -150)
    fcc_offset3.inputs["Translation"].default_value = (0.0, 0.5, 0.5)
    links.new(base_points.outputs["Geometry"], fcc_offset3.inputs["Geometry"])

    fcc_join = nodes.new('GeometryNodeJoinGeometry')
    fcc_join.location = (400, 0)
    links.new(base_points.outputs["Geometry"], fcc_join.inputs["Geometry"])
    links.new(fcc_offset1.outputs["Geometry"], fcc_join.inputs["Geometry"])
    links.new(fcc_offset2.outputs["Geometry"], fcc_join.inputs["Geometry"])
    links.new(fcc_offset3.outputs["Geometry"], fcc_join.inputs["Geometry"])

    # Select Switch
    switch_bcc = nodes.new('GeometryNodeSwitch')
    switch_bcc.input_type = 'GEOMETRY'
    switch_bcc.location = (600, 250)
    links.new(base_points.outputs["Geometry"], switch_bcc.inputs["False"])
    links.new(bcc_join.outputs["Geometry"], switch_bcc.inputs["True"])

    cmp_bcc = nodes.new('FunctionNodeCompare')
    cmp_bcc.data_type = 'INT'
    cmp_bcc.operation = 'EQUAL'
    cmp_bcc.location = (400, 400)
    cmp_bcc.inputs[3].default_value = 1 # BCC (index 2 is A, 3 is B for Int)
    links.new(group_in.outputs["Crystal System"], cmp_bcc.inputs[2])
    links.new(cmp_bcc.outputs["Result"], switch_bcc.inputs["Switch"])

    switch_fcc = nodes.new('GeometryNodeSwitch')
    switch_fcc.input_type = 'GEOMETRY'
    switch_fcc.location = (800, 250)
    links.new(switch_bcc.outputs["Output"], switch_fcc.inputs["False"])
    links.new(fcc_join.outputs["Geometry"], switch_fcc.inputs["True"])

    cmp_fcc = nodes.new('FunctionNodeCompare')
    cmp_fcc.data_type = 'INT'
    cmp_fcc.operation = 'EQUAL'
    cmp_fcc.location = (600, 400)
    cmp_fcc.inputs[3].default_value = 2 # FCC
    links.new(group_in.outputs["Crystal System"], cmp_fcc.inputs[2])
    links.new(cmp_fcc.outputs["Result"], switch_fcc.inputs["Switch"])

    # We will pass switch_fcc as our base points to the scaler
    lattice_geom = switch_fcc

    # Scale points based on lattice constant (A, and possibly C for Z axis)
    # X and Y scaled by A, Z scaled by C (for simplicity in SC/HCP distinction)
    scale_pos = nodes.new('GeometryNodeSetPosition')
    scale_pos.location = (1000, 250)

    position_node = nodes.new('GeometryNodeInputPosition')
    position_node.location = (600, 50)

    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (800, 50)
    links.new(position_node.outputs["Position"], sep_xyz.inputs["Vector"])

    comb_xyz = nodes.new('ShaderNodeCombineXYZ')
    comb_xyz.location = (1000, 50)

    math_x = nodes.new('ShaderNodeMath')
    math_x.operation = 'MULTIPLY'
    math_x.location = (800, -100)
    links.new(sep_xyz.outputs["X"], math_x.inputs[0])
    links.new(group_in.outputs["Lattice Constant A"], math_x.inputs[1])

    math_y = nodes.new('ShaderNodeMath')
    math_y.operation = 'MULTIPLY'
    math_y.location = (800, -250)
    links.new(sep_xyz.outputs["Y"], math_y.inputs[0])
    links.new(group_in.outputs["Lattice Constant A"], math_y.inputs[1])

    math_z = nodes.new('ShaderNodeMath')
    math_z.operation = 'MULTIPLY'
    math_z.location = (800, -400)
    links.new(sep_xyz.outputs["Z"], math_z.inputs[0])
    links.new(group_in.outputs["Lattice Constant C"], math_z.inputs[1])

    links.new(math_x.outputs["Value"], comb_xyz.inputs["X"])
    links.new(math_y.outputs["Value"], comb_xyz.inputs["Y"])
    links.new(math_z.outputs["Value"], comb_xyz.inputs["Z"])

    links.new(comb_xyz.outputs["Vector"], scale_pos.inputs["Position"])
    links.new(lattice_geom.outputs["Output"], scale_pos.inputs["Geometry"])

    # Thermal vibration (Noise)
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (1000, -550)
    noise.inputs["Scale"].default_value = 10.0

    scene_time = nodes.new('GeometryNodeInputSceneTime')
    scene_time.location = (800, -550)
    links.new(scene_time.outputs["Seconds"], noise.inputs["W"])
    noise.noise_dimensions = '4D'

    sub_noise = nodes.new('ShaderNodeVectorMath')
    sub_noise.operation = 'SUBTRACT'
    sub_noise.location = (1200, -550)
    links.new(noise.outputs["Color"], sub_noise.inputs[0])
    sub_noise.inputs[1].default_value = (0.5, 0.5, 0.5)

    scale_noise = nodes.new('ShaderNodeVectorMath')
    scale_noise.operation = 'SCALE'
    scale_noise.location = (1400, -550)
    links.new(sub_noise.outputs["Vector"], scale_noise.inputs[0])
    links.new(group_in.outputs["Temperature"], scale_noise.inputs["Scale"])

    set_vibration = nodes.new('GeometryNodeSetPosition')
    set_vibration.location = (1200, 250)
    links.new(scale_pos.outputs["Geometry"], set_vibration.inputs["Geometry"])
    links.new(scale_noise.outputs["Vector"], set_vibration.inputs["Offset"])

    # Apply strain (simple X-axis scale as an example)
    strain_math = nodes.new('ShaderNodeMath')
    strain_math.operation = 'ADD'
    strain_math.location = (1000, 350)
    strain_math.inputs[0].default_value = 1.0
    links.new(group_in.outputs["Strain"], strain_math.inputs[1])

    strain_vec = nodes.new('ShaderNodeCombineXYZ')
    strain_vec.location = (1200, 450)
    links.new(strain_math.outputs["Value"], strain_vec.inputs["X"])
    strain_vec.inputs["Y"].default_value = 1.0
    strain_vec.inputs["Z"].default_value = 1.0

    apply_strain = nodes.new('GeometryNodeTransform')
    apply_strain.location = (1400, 250)
    links.new(set_vibration.outputs["Geometry"], apply_strain.inputs["Geometry"])
    links.new(strain_vec.outputs["Vector"], apply_strain.inputs["Scale"])

    # Defects: Delete points based on concentration
    delete_geom = nodes.new('GeometryNodeDeleteGeometry')
    delete_geom.location = (1600, 250)
    links.new(apply_strain.outputs["Geometry"], delete_geom.inputs["Geometry"])

    random_val = nodes.new('GeometryNodeRandomValue')
    random_val.data_type = 'FLOAT'
    random_val.location = (1400, 50)

    compare = nodes.new('FunctionNodeCompare')
    compare.data_type = 'FLOAT'
    compare.operation = 'LESS_THAN'
    compare.location = (1600, 50)
    links.new(random_val.outputs["Value"], compare.inputs[0])
    links.new(group_in.outputs["Defect Concentration"], compare.inputs[1])
    links.new(compare.outputs["Result"], delete_geom.inputs["Selection"])

    # Instance atoms (Icospheres)
    atom_mesh = nodes.new('GeometryNodeMeshIcoSphere')
    atom_mesh.location = (1600, -250)
    atom_mesh.inputs["Radius"].default_value = 0.1
    atom_mesh.inputs["Subdivisions"].default_value = 2

    final_inst = nodes.new('GeometryNodeInstanceOnPoints')
    final_inst.location = (1800, 250)
    links.new(delete_geom.outputs["Geometry"], final_inst.inputs["Points"])
    links.new(atom_mesh.outputs["Mesh"], final_inst.inputs["Instance"])

    # Output
    group_out.location = (2000, 250)
    links.new(final_inst.outputs["Instances"], group_out.inputs["Geometry"])

    return group

class CrystalProperties(bpy.types.PropertyGroup):
    crystal_system: bpy.props.EnumProperty(
        name="Crystal System",
        description="Select the crystal system",
        items=[
            ('SC', "Simple Cubic", "Simple Cubic Lattice"),
            ('BCC', "BCC", "Body-Centered Cubic"),
            ('FCC', "FCC", "Face-Centered Cubic"),
        ],
        default='SC'
    )

    lattice_constant_a: bpy.props.FloatProperty(
        name="Lattice Constant A",
        description="Lattice constant A (nm)",
        default=0.5,
        min=0.1,
        max=5.0
    )

    lattice_constant_c: bpy.props.FloatProperty(
        name="Lattice Constant C",
        description="Lattice constant C (nm), used for HCP/MXene",
        default=0.8,
        min=0.1,
        max=5.0
    )

    supercell_x: bpy.props.IntProperty(name="Supercell X", default=3, min=1, max=50)
    supercell_y: bpy.props.IntProperty(name="Supercell Y", default=3, min=1, max=50)
    supercell_z: bpy.props.IntProperty(name="Supercell Z", default=3, min=1, max=50)

    temperature: bpy.props.FloatProperty(
        name="Temperature",
        description="Simulate thermal vibration magnitude",
        default=0.0,
        min=0.0,
        max=1.0
    )

    defect_concentration: bpy.props.FloatProperty(
        name="Defect Concentration",
        description="Probability of vacancy defects",
        default=0.0,
        min=0.0,
        max=1.0
    )


    strain: bpy.props.FloatProperty(
        name="Strain",
        description="Apply uniaxial strain",
        default=0.0,
        min=-0.5,
        max=0.5
    )

class CRYSTAL_OT_generate(bpy.types.Operator):
    bl_idname = "crystal.generate"
    bl_label = "Generate Crystal"
    bl_description = "Generates a procedural crystal based on current parameters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.crystal_props

        # Create a new object to hold the crystal
        mesh = bpy.data.meshes.new("Crystal_Mesh")
        obj = bpy.data.objects.new(f"{props.crystal_system}_Crystal", mesh)
        context.collection.objects.link(obj)

        # Add Geometry Nodes Modifier
        mod = obj.modifiers.new(name="Crystal_Gen", type='NODES')
        node_group = create_crystal_geometry_nodes()
        mod.node_group = node_group

        # We access inputs safely, Blender 3.x+ syntax
        # For Blender 3.3, modifier input mapping is via node_group.inputs.
        # Find exactly which modifier string key matches the input.
        # Often in Blender 3.x, modifier properties directly match the input string or are Input_#

        # We just iterate over the keys that exist in the modifier which are generated for GN inputs.
        sys_map = {
            'SC': 0,
            'BCC': 1,
            'FCC': 2,
        }
        sys_val = sys_map.get(props.crystal_system, 0)

        # In Blender 3.3, it is safe to assign by iterating group inputs
        # and finding the identifier in the modifier keys:
        input_name_to_val = {
            "Crystal System": sys_val,
            "Supercell X": props.supercell_x,
            "Supercell Y": props.supercell_y,
            "Supercell Z": props.supercell_z,
            "Lattice Constant A": props.lattice_constant_a,
            "Lattice Constant C": props.lattice_constant_c,
            "Temperature": props.temperature,
            "Defect Concentration": props.defect_concentration,
            "Strain": props.strain
        }

        # Map input names to identifier using node_group.inputs
        input_identifier = {}
        for inp in node_group.inputs:
            input_identifier[inp.name] = inp.identifier

        for name, val in input_name_to_val.items():
            if name in input_identifier:
                identifier = input_identifier[name]
                # Modifiers dynamically expose these properties, mod.keys() may be empty until set.
                # In Blender Python, we can just assign directly using dictionary access if the property exists conceptually.
                try:
                    mod[identifier] = val
                except KeyError:
                    # Fallback if standard string names are preferred over identifier string
                    try:
                        mod[name] = val
                    except KeyError:
                        pass

        # Select the newly created object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        self.report({'INFO'}, f"Generated {props.crystal_system} Crystal")
        return {'FINISHED'}

class CRYSTAL_PT_panel(bpy.types.Panel):
    bl_label = "Crystal Generator"
    bl_idname = "CRYSTAL_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Crystal'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        crystal_props = scene.crystal_props

        layout.prop(crystal_props, "crystal_system")

        row = layout.row()
        row.prop(crystal_props, "lattice_constant_a")

        layout.label(text="Supercell Dimensions:")
        row = layout.row(align=True)
        row.prop(crystal_props, "supercell_x", text="X")
        row.prop(crystal_props, "supercell_y", text="Y")
        row.prop(crystal_props, "supercell_z", text="Z")

        layout.label(text="Physics & Simulation:")
        layout.prop(crystal_props, "temperature")
        layout.prop(crystal_props, "defect_concentration")
        layout.prop(crystal_props, "strain")

        layout.operator("crystal.generate", text="Generate Crystal", icon='MESH_ICOSPHERE')


classes = (
    CrystalProperties,
    CRYSTAL_OT_generate,
    CRYSTAL_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.crystal_props = bpy.props.PointerProperty(type=CrystalProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "crystal_props"):
        del bpy.types.Scene.crystal_props

if __name__ == "__main__":
    register()
