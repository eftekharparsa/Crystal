bl_info = {
    "name": "Crystal Procedural Generator",
    "author": "Jules",
    "version": (1, 1),
    "blender": (4, 0, 0),
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
    group_name = "Crystal_Procedural_Generator_V3"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    group = bpy.data.node_groups.new(name=group_name, type='GeometryNodeTree')

    # Inputs
    inp_sx = group.interface.new_socket(name="Supercell X", in_out='INPUT', socket_type='NodeSocketInt')
    inp_sy = group.interface.new_socket(name="Supercell Y", in_out='INPUT', socket_type='NodeSocketInt')
    inp_sz = group.interface.new_socket(name="Supercell Z", in_out='INPUT', socket_type='NodeSocketInt')
    inp_la = group.interface.new_socket(name="Lattice Constant A", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_lc = group.interface.new_socket(name="Lattice Constant C", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_temp = group.interface.new_socket(name="Temperature", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_freq = group.interface.new_socket(name="Oscillation Frequency", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_def = group.interface.new_socket(name="Defect Concentration", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_str = group.interface.new_socket(name="Strain", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_csys = group.interface.new_socket(name="Crystal System", in_out='INPUT', socket_type='NodeSocketInt')
    inp_mh = group.interface.new_socket(name="Miller H", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_mk = group.interface.new_socket(name="Miller K", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_ml = group.interface.new_socket(name="Miller L", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_cd = group.interface.new_socket(name="Cut Distance", in_out='INPUT', socket_type='NodeSocketFloat')
    inp_is2d = group.interface.new_socket(name="Is 2D", in_out='INPUT', socket_type='NodeSocketBool')
    inp_bond = group.interface.new_socket(name="Show Bonds", in_out='INPUT', socket_type='NodeSocketBool')
    inp_diat = group.interface.new_socket(name="Diatomic Basis", in_out='INPUT', socket_type='NodeSocketBool')
    inp_obj1 = group.interface.new_socket(name="Atom 1", in_out='INPUT', socket_type='NodeSocketObject')
    inp_obj2 = group.interface.new_socket(name="Atom 2", in_out='INPUT', socket_type='NodeSocketObject')
    inp_use1 = group.interface.new_socket(name="Use Atom 1", in_out='INPUT', socket_type='NodeSocketBool')
    inp_use2 = group.interface.new_socket(name="Use Atom 2", in_out='INPUT', socket_type='NodeSocketBool')

    inp_sx.default_value = 3
    inp_sy.default_value = 3
    inp_sz.default_value = 3
    inp_la.default_value = 0.5
    inp_lc.default_value = 0.8
    inp_temp.default_value = 0.0
    inp_freq.default_value = 1.0
    inp_def.default_value = 0.0
    inp_str.default_value = 0.0
    inp_csys.default_value = 0

    # Outputs
    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = group.nodes
    links = group.links

    # Node setup
    group_in = nodes.new('NodeGroupInput')
    group_in.location = (-800, 0)

    group_out = nodes.new('NodeGroupOutput')
    group_out.location = (800, 0)

    # Force Z to 1 if 2D Material
    switch_z = nodes.new('GeometryNodeSwitch')
    switch_z.input_type = 'INT'
    switch_z.location = (-800, 200)
    links.new(group_in.outputs["Is 2D"], switch_z.inputs["Switch"])
    links.new(group_in.outputs["Supercell Z"], switch_z.inputs["False"])
    switch_z.inputs["True"].default_value = 1

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
    links.new(switch_z.outputs["Output"], line_z.inputs["Count"])

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
    noise.noise_dimensions = '4D'
    noise.inputs["Scale"].default_value = 10.0

    scene_time = nodes.new('GeometryNodeInputSceneTime')
    scene_time.location = (600, -550)

    math_freq = nodes.new('ShaderNodeMath')
    math_freq.operation = 'MULTIPLY'
    math_freq.location = (800, -550)
    links.new(scene_time.outputs["Seconds"], math_freq.inputs[0])
    links.new(group_in.outputs["Oscillation Frequency"], math_freq.inputs[1])

    links.new(math_freq.outputs["Value"], noise.inputs["W"])

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

    # Miller Plane Cut
    miller_cut = nodes.new('GeometryNodeDeleteGeometry')
    miller_cut.location = (1600, 250)
    links.new(apply_strain.outputs["Geometry"], miller_cut.inputs["Geometry"])

    pos_cut = nodes.new('GeometryNodeInputPosition')
    pos_cut.location = (1200, 100)

    comb_miller = nodes.new('ShaderNodeCombineXYZ')
    comb_miller.location = (1200, 0)
    links.new(group_in.outputs["Miller H"], comb_miller.inputs["X"])
    links.new(group_in.outputs["Miller K"], comb_miller.inputs["Y"])
    links.new(group_in.outputs["Miller L"], comb_miller.inputs["Z"])

    dot_miller = nodes.new('ShaderNodeVectorMath')
    dot_miller.operation = 'DOT_PRODUCT'
    dot_miller.location = (1400, 50)
    links.new(pos_cut.outputs["Position"], dot_miller.inputs[0])
    links.new(comb_miller.outputs["Vector"], dot_miller.inputs[1])

    cmp_cut = nodes.new('FunctionNodeCompare')
    cmp_cut.data_type = 'FLOAT'
    cmp_cut.operation = 'GREATER_THAN'
    cmp_cut.location = (1600, 50)
    links.new(dot_miller.outputs["Value"], cmp_cut.inputs[0])
    links.new(group_in.outputs["Cut Distance"], cmp_cut.inputs[1])

    # We only cut if the user actually specified a plane (e.g. any miller index != 0)
    len_miller = nodes.new('ShaderNodeVectorMath')
    len_miller.operation = 'LENGTH'
    len_miller.location = (1400, -100)
    links.new(comb_miller.outputs["Vector"], len_miller.inputs[0])

    cmp_len = nodes.new('FunctionNodeCompare')
    cmp_len.data_type = 'FLOAT'
    cmp_len.operation = 'GREATER_THAN'
    cmp_len.location = (1600, -100)
    links.new(len_miller.outputs["Value"], cmp_len.inputs[0])
    cmp_len.inputs[1].default_value = 0.001

    and_cut = nodes.new('FunctionNodeBooleanMath')
    and_cut.operation = 'AND'
    and_cut.location = (1800, 0)
    links.new(cmp_cut.outputs["Result"], and_cut.inputs[0])
    links.new(cmp_len.outputs["Result"], and_cut.inputs[1])
    links.new(and_cut.outputs["Boolean"], miller_cut.inputs["Selection"])

    # Defects: Delete points based on concentration
    delete_geom = nodes.new('GeometryNodeDeleteGeometry')
    delete_geom.location = (1800, 250)
    links.new(miller_cut.outputs["Geometry"], delete_geom.inputs["Geometry"])

    random_val = nodes.new('FunctionNodeRandomValue')
    random_val.data_type = 'FLOAT'
    random_val.location = (1600, -250)

    compare_def = nodes.new('FunctionNodeCompare')
    compare_def.data_type = 'FLOAT'
    compare_def.operation = 'LESS_THAN'
    compare_def.location = (1800, -250)
    links.new(random_val.outputs["Value"], compare_def.inputs[0])
    links.new(group_in.outputs["Defect Concentration"], compare_def.inputs[1])
    links.new(compare_def.outputs["Result"], delete_geom.inputs["Selection"])

    # Store base points for bonds
    base_atoms = delete_geom

    # Instance atoms (Diatomic or Monatomic)
    atom_mesh = nodes.new('GeometryNodeMeshIcoSphere')
    atom_mesh.location = (1800, -500)
    atom_mesh.inputs["Radius"].default_value = 0.1
    atom_mesh.inputs["Subdivisions"].default_value = 2

    obj_info1 = nodes.new('GeometryNodeObjectInfo')
    obj_info1.location = (1800, -650)
    links.new(group_in.outputs["Atom 1"], obj_info1.inputs["Object"])

    switch_inst1 = nodes.new('GeometryNodeSwitch')
    switch_inst1.input_type = 'GEOMETRY'
    switch_inst1.location = (2000, -500)
    links.new(atom_mesh.outputs["Mesh"], switch_inst1.inputs["False"])
    links.new(obj_info1.outputs["Geometry"], switch_inst1.inputs["True"])
    links.new(group_in.outputs["Use Atom 1"], switch_inst1.inputs["Switch"])

    final_inst = nodes.new('GeometryNodeInstanceOnPoints')
    final_inst.location = (2200, 250)
    links.new(base_atoms.outputs["Geometry"], final_inst.inputs["Points"])

    # Diatomic Basis logic
    obj_info2 = nodes.new('GeometryNodeObjectInfo')
    obj_info2.location = (1800, -800)
    links.new(group_in.outputs["Atom 2"], obj_info2.inputs["Object"])

    switch_inst2 = nodes.new('GeometryNodeSwitch')
    switch_inst2.input_type = 'GEOMETRY'
    switch_inst2.location = (2000, -650)
    links.new(atom_mesh.outputs["Mesh"], switch_inst2.inputs["False"])
    links.new(obj_info2.outputs["Geometry"], switch_inst2.inputs["True"])
    links.new(group_in.outputs["Use Atom 2"], switch_inst2.inputs["Switch"])

    idx_node = nodes.new('GeometryNodeInputIndex')
    idx_node.location = (1800, -350)

    math_mod = nodes.new('ShaderNodeMath')
    math_mod.operation = 'MODULO'
    math_mod.location = (2000, -350)
    links.new(idx_node.outputs["Index"], math_mod.inputs[0])
    math_mod.inputs[1].default_value = 2.0

    cmp_diat = nodes.new('FunctionNodeCompare')
    cmp_diat.data_type = 'FLOAT'
    cmp_diat.operation = 'EQUAL'
    cmp_diat.location = (2200, -350)
    links.new(math_mod.outputs["Value"], cmp_diat.inputs[0])
    cmp_diat.inputs[1].default_value = 1.0

    # Separate points for Atom 1 and Atom 2
    sep_points = nodes.new('GeometryNodeSeparateGeometry')
    sep_points.domain = 'POINT'
    sep_points.location = (2400, 250)
    links.new(base_atoms.outputs["Geometry"], sep_points.inputs["Geometry"])

    # Boolean logic: If Diatomic, separate by modulo. If Monatomic, all go to Atom 1.
    and_diat = nodes.new('FunctionNodeBooleanMath')
    and_diat.operation = 'AND'
    and_diat.location = (2400, 50)
    links.new(cmp_diat.outputs["Result"], and_diat.inputs[0])
    links.new(group_in.outputs["Diatomic Basis"], and_diat.inputs[1])
    links.new(and_diat.outputs["Boolean"], sep_points.inputs["Selection"])

    inst1 = nodes.new('GeometryNodeInstanceOnPoints')
    inst1.location = (2600, 400)
    links.new(sep_points.outputs["Inverted"], inst1.inputs["Points"])
    links.new(switch_inst1.outputs["Output"], inst1.inputs["Instance"])

    inst2 = nodes.new('GeometryNodeInstanceOnPoints')
    inst2.location = (2600, 200)
    links.new(sep_points.outputs["Selection"], inst2.inputs["Points"])
    links.new(switch_inst2.outputs["Output"], inst2.inputs["Instance"])

    join_insts = nodes.new('GeometryNodeJoinGeometry')
    join_insts.location = (2800, 300)
    links.new(inst1.outputs["Instances"], join_insts.inputs["Geometry"])
    links.new(inst2.outputs["Instances"], join_insts.inputs["Geometry"])

    # Bonds visualization
    # Generating edges from point clouds in pure GN is complex. A simple approach for
    # cubic lattices is to use the Points to Volume trick, or simply use
    # the original mesh lines but we must make sure edges exist in X, Y, Z.
    # For now, to keep the tree from becoming massive, we'll connect points via proximity.

    # A simple but effective trick for bond generation from points:
    # Instance a thin cylinder on every point, aligned to neighbors.
    # Or rely on VolumeToMesh as before which creates a continuous web.
    # Since VolumeToMesh is heavy, we'll use a bounding-box volume approach.

    pt_vol = nodes.new('GeometryNodePointsToVolume')
    pt_vol.location = (2600, -100)
    pt_vol.inputs["Radius"].default_value = 0.15 # Approx half a bond
    links.new(base_atoms.outputs["Geometry"], pt_vol.inputs["Points"])

    vol_mesh = nodes.new('GeometryNodeVolumeToMesh')
    vol_mesh.location = (2800, -100)
    links.new(pt_vol.outputs["Volume"], vol_mesh.inputs["Volume"])

    mesh_curve = nodes.new('GeometryNodeMeshToCurve')
    mesh_curve.location = (3000, -100)
    links.new(vol_mesh.outputs["Mesh"], mesh_curve.inputs["Mesh"])

    curve_mesh = nodes.new('GeometryNodeCurveToMesh')
    curve_mesh.location = (3200, -100)
    links.new(mesh_curve.outputs["Curve"], curve_mesh.inputs["Curve"])

    bond_profile = nodes.new('GeometryNodeCurvePrimitiveCircle')
    bond_profile.location = (3000, -250)
    bond_profile.inputs["Radius"].default_value = 0.03
    bond_profile.inputs["Resolution"].default_value = 6
    links.new(bond_profile.outputs["Curve"], curve_mesh.inputs["Profile Curve"])

    bond_switch = nodes.new('GeometryNodeSwitch')
    bond_switch.input_type = 'GEOMETRY'
    bond_switch.location = (3400, 100)
    links.new(group_in.outputs["Show Bonds"], bond_switch.inputs["Switch"])
    links.new(curve_mesh.outputs["Mesh"], bond_switch.inputs["True"])

    join_final = nodes.new('GeometryNodeJoinGeometry')
    join_final.location = (3600, 250)
    links.new(join_insts.outputs["Geometry"], join_final.inputs["Geometry"])
    links.new(bond_switch.outputs["Output"], join_final.inputs["Geometry"])

    # Output
    group_out.location = (3800, 250)
    links.new(join_final.outputs["Geometry"], group_out.inputs["Geometry"])

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

    oscillation_frequency: bpy.props.FloatProperty(
        name="Oscillation Frequency",
        description="Frequency of thermal oscillation",
        default=1.0,
        min=0.0,
        max=10.0
    )

    show_bonds: bpy.props.BoolProperty(
        name="Show Bonds",
        description="Visualize atomic bonds",
        default=False
    )

    diatomic_basis: bpy.props.BoolProperty(
        name="Diatomic Basis",
        description="Use two different atoms for the basis (e.g. NaCl)",
        default=False
    )

    atom_1_instance: bpy.props.PointerProperty(
        name="Atom 1 Object",
        type=bpy.types.Object,
        description="Custom object for atom 1"
    )

    atom_2_instance: bpy.props.PointerProperty(
        name="Atom 2 Object",
        type=bpy.types.Object,
        description="Custom object for atom 2 (if Diatomic)"
    )

    is_2d_material: bpy.props.BoolProperty(
        name="2D Material",
        description="Force 2D structure (Supercell Z=1)",
        default=False
    )

    miller_h: bpy.props.FloatProperty(name="Miller h", default=0.0)
    miller_k: bpy.props.FloatProperty(name="Miller k", default=0.0)
    miller_l: bpy.props.FloatProperty(name="Miller l", default=0.0)
    cut_distance: bpy.props.FloatProperty(name="Cut Distance", default=0.0)

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
            "Oscillation Frequency": props.oscillation_frequency,
            "Defect Concentration": props.defect_concentration,
            "Strain": props.strain,
            "Miller H": props.miller_h,
            "Miller K": props.miller_k,
            "Miller L": props.miller_l,
            "Cut Distance": props.cut_distance,
            "Is 2D": props.is_2d_material,
            "Show Bonds": props.show_bonds,
            "Diatomic Basis": props.diatomic_basis,
            "Atom 1": props.atom_1_instance,
            "Atom 2": props.atom_2_instance,
            "Use Atom 1": props.atom_1_instance is not None,
            "Use Atom 2": props.atom_2_instance is not None,
        }

        # Mapping input names to their identifiers in the modifier (Blender 4.0+)
        input_identifier = {}
        for identifier, socket in node_group.interface.items_tree.items():
            if socket.item_type == 'SOCKET' and socket.in_out == 'INPUT':
                input_identifier[socket.name] = identifier

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

        layout.prop(crystal_props, "is_2d_material")

        layout.label(text="Supercell Dimensions:")
        row = layout.row(align=True)
        row.prop(crystal_props, "supercell_x", text="X")
        row.prop(crystal_props, "supercell_y", text="Y")
        if not crystal_props.is_2d_material:
            row.prop(crystal_props, "supercell_z", text="Z")

        layout.label(text="Appearance:")
        layout.prop(crystal_props, "diatomic_basis")
        layout.prop(crystal_props, "atom_1_instance")
        if crystal_props.diatomic_basis:
            layout.prop(crystal_props, "atom_2_instance")
        layout.prop(crystal_props, "show_bonds")

        layout.label(text="Plane Cut (Miller Indices):")
        row = layout.row(align=True)
        row.prop(crystal_props, "miller_h", text="h")
        row.prop(crystal_props, "miller_k", text="k")
        row.prop(crystal_props, "miller_l", text="l")
        layout.prop(crystal_props, "cut_distance")

        layout.label(text="Physics & Simulation:")
        layout.prop(crystal_props, "temperature")
        layout.prop(crystal_props, "oscillation_frequency")
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
