"""
lookdev Turntable Rig Python Script (for Houdini & Mantra)
by Megan White 
July 2025

"""

import hou
from PySide2 import QtWidgets, QtCore
import os
import math
import json


### retrieve previously used settings for UI inputs 
def get_settings_path():
    prefs_dir = hou.expandString("$HOUDINI_USER_PREF_DIR")
    return os.path.join(prefs_dir, "lookdev_rig_settings.json")

def load_settings():
    path = get_settings_path()
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

### save UI input settings for future uses    
def save_settings(settings):
    path = get_settings_path()
    try:
        with open(path, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass

### Build UI        
class LookdevRigUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LookdevRigUI, self).__init__(parent)
        self.setWindowTitle("LookDev Light Rig Setup")
        self.setMinimumWidth(400)

        settings = load_settings()

        # HDRI File Path
        self.hdri_label = QtWidgets.QLabel("HDRI File (.exr):")
        self.hdri_input = QtWidgets.QLineEdit(settings.get("hdri_path", ""))
        self.hdri_browse = QtWidgets.QPushButton("Browse")
        self.hdri_browse.clicked.connect(self.browse_hdri)
        hdri_layout = QtWidgets.QHBoxLayout()
        hdri_layout.addWidget(self.hdri_input)
        hdri_layout.addWidget(self.hdri_browse)

        # Object rotation inputs
        self.rotation_label = QtWidgets.QLabel("Rotation Offset")
        self.rotation_input = QtWidgets.QDoubleSpinBox()
        self.rotation_input.setRange(-1e6, 1e6)
        self.rotation_input.setDecimals(3)
        self.rotation_input.setValue(settings.get("rotation_offset", 0.0))

        # HDRI rotation inputs
        self.light_rotation_label = QtWidgets.QLabel("HDRI Rotation Offset")
        self.light_rotation_input = QtWidgets.QDoubleSpinBox()
        self.light_rotation_input.setRange(-1e6, 1e6)
        self.light_rotation_input.setDecimals(3)
        self.light_rotation_input.setValue(settings.get("hdri_rotation_offset", 0.0))

        # Sweep checkbox
        self.sweep_checkbox = QtWidgets.QCheckBox("Background Geo Enabled")
        self.sweep_checkbox.setChecked(settings.get("sweep_enabled", True))

        # Lookdev Ref Kit checkbox
        self.refkit_checkbox = QtWidgets.QCheckBox("Add Lookdev Reference Kit")
        self.refkit_checkbox.setChecked(settings.get("add_refkit", True))

        # Macbeth texture path with browse button
        self.macbeth_label = QtWidgets.QLabel("Macbeth Chart Texture:")
        self.macbeth_input = QtWidgets.QLineEdit(settings.get("macbeth_path", ""))
        self.macbeth_browse = QtWidgets.QPushButton("Browse")
        self.macbeth_browse.clicked.connect(self.browse_macbeth)
        macbeth_layout = QtWidgets.QHBoxLayout()
        macbeth_layout.addWidget(self.macbeth_input)
        macbeth_layout.addWidget(self.macbeth_browse)
        
        #start frame
        self.start_frame_label = QtWidgets.QLabel("Start Frame")
        self.start_frame_input = QtWidgets.QSpinBox()
        self.start_frame_input.setRange(1, 100000)
        self.start_frame_input.setValue(1001)  # Default value
        

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.hdri_label)
        layout.addLayout(hdri_layout)
        layout.addWidget(self.rotation_label)
        layout.addWidget(self.rotation_input)
        layout.addWidget(self.light_rotation_label)
        layout.addWidget(self.light_rotation_input)
        layout.addWidget(self.sweep_checkbox)
        layout.addWidget(self.refkit_checkbox)
        layout.addWidget(self.macbeth_label)
        layout.addLayout(macbeth_layout)
        layout.addWidget(self.start_frame_label)
        layout.addWidget(self.start_frame_input)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    #file browser for HDRI image
    def browse_hdri(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select HDRI File", "", "EXR Files (*.exr)")
        if path:
            self.hdri_input.setText(path)

    #file browser for macbeth chart texture          
    def browse_macbeth(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Macbeth Texture", "", "Image Files (*.jpg *.jpeg *.png *.tif *.tiff)")
        if path:
            self.macbeth_input.setText(path)

    #return values for rig setup
    def get_values(self):
        return {
            "hdri_path": self.hdri_input.text(),
            "rotation_offset": self.rotation_input.value(),
            "hdri_rotation_offset": self.light_rotation_input.value(),
            "sweep_enabled": self.sweep_checkbox.isChecked(),
            "add_refkit": self.refkit_checkbox.isChecked(),
            "macbeth_path": self.macbeth_input.text(),
            "start_frame": int(self.start_frame_input.text())
        }

        
### function for simplifying keyframing process        
def create_keyframe(parm, value, frame):
    key = hou.Keyframe()
    key.setFrame(frame)
    key.setValue(value)
    parm.setKeyframe(key)

### Add turntable animation for camera from frames 1001 - 1100   
def update_camera_animation(cam, center, cam_distance, initial_angle, start_frame):
    for parm_name in ("tx", "ty", "tz"):
        cam.parm(parm_name).deleteAllKeyframes()

    #calculate rotation of camera around the selected object
    for f in range(start_frame, start_frame + 101):
        t = (f - start_frame) / 99.0
        angle_deg = initial_angle + t * 360
        angle_rad = math.radians(angle_deg)
        cam_x = center[0] + cam_distance * math.sin(angle_rad)
        cam_z = center[2] + cam_distance * math.cos(angle_rad)
        cam_y = center[1]
        create_keyframe(cam.parm("tx"), cam_x, f)
        create_keyframe(cam.parm("ty"), cam_y, f)
        create_keyframe(cam.parm("tz"), cam_z, f)
 
### Add turntable animation for sweep geo from frames 1001 - 1100 
def update_sweep_animation(null, center, cam_distance, initial_angle, start_frame):
    for parm_name in ("tx", "ty", "tz"):
        null.parm(parm_name).deleteAllKeyframes()
        
    #calculate rotation of sweep around the selected object (matching camera)
    for f in range(start_frame, start_frame + 101):
        t = (f - start_frame) / 99.0
        angle_deg = initial_angle + t * 360
        angle_rad = math.radians(angle_deg)
        null_x = center[0] + cam_distance * math.sin(angle_rad)
        null_z = center[2] + cam_distance * math.cos(angle_rad)
        null_y = center[1]
        create_keyframe(null.parm("tx"), null_x, f)
        create_keyframe(null.parm("ty"), null_y, f)
        create_keyframe(null.parm("tz"), null_z, f)
        


### Add turntable rotation for hdri light (should match object for 1001 - 1100 and should rotate from 1101 - 1200         
def update_envlight_animation(env_light, initial_angle, hdri_rotation, start_frame):
    ry = env_light.parm("ry")
    ry.deleteAllKeyframes()
    base = initial_angle + 180
    create_keyframe(ry, base - 360, start_frame)
    create_keyframe(ry, base, start_frame + 99)
    create_keyframe(ry, base - 360, start_frame + 199)

    
    
    
### model the backdrop sweep geo    
def create_sweep(size, center, cam_distance):
    sweep_geo = hou.node("/obj").createNode("geo", "lookdev_sweep")
    for c in sweep_geo.children(): c.destroy()

    # sweep geo dimensions 
    arc_radius = max(size[0], size[1], size[2]) * 4
    sweep_width = max(size[0], size[1], size[2]) * 10
    floor_len = cam_distance/4
    object_base = center[1] - (size[1]/2)

    #create arc for sweep angle and orient towards camera
    arc = sweep_geo.createNode("circle", "arc")
    arc.parm("type").set(1)
    arc.parm("arc").set(True)
    arc.parm("orient").set(3)
    arc.parm("beginangle").set(0)
    arc.parm("endangle").set(90)
    arc.parm("scale").set(arc_radius)
    arc.parm("divs").set(16)
    arc.parm("ry").set(90)
    arc.parm("rz").set(-90)
    arc.parm("ty").set(object_base + arc_radius)
    
    #move away from camera
    move_arc = sweep_geo.createNode("xform", "offset_arc")
    move_arc.setInput(0, arc)
    move_arc.parmTuple("t").set((0, 0, -floor_len))

    #extrude into sweep
    extrude = sweep_geo.createNode("polyextrude", "extrude")
    extrude.setInput(0, move_arc)
    extrude.parm("translatex").set(sweep_width)
    extrude.parm("outputfront").set(True)
    extrude.parm("xformfront").set(True)
    extrude.parm("xformspace").set("global")

    #shift to center geo
    shift = sweep_geo.createNode("xform", "shift")
    shift.setInput(0, extrude)
    shift.parm("tx").set(-sweep_width/2)

    #add floor grid that lines up with sweep
    floor = sweep_geo.createNode("grid", "floor")
    floor.parm("sizex").set(sweep_width)
    floor.parm("sizey").set(floor_len * 4)
    floor.parm("tz").set(floor_len)
    floor.parm("ty").set(object_base)
    floor.parm("rows").set(2)
    floor.parm("cols").set(2)

    #merge and fuse floor with sweep
    merge = sweep_geo.createNode("merge", "merge")
    merge.setNextInput(floor)
    merge.setNextInput(shift)
    fuse = sweep_geo.createNode("fuse", "fuse")
    fuse.setInput(0, merge)

    #subdivide to smooth out
    subdiv = sweep_geo.createNode("subdivide", "subdivide")
    subdiv.setInput(0, fuse)
    
    #move to object location
    centered = sweep_geo.createNode("xform", "center")
    centered.setInput(0, subdiv)
    centered.parm("tx").set(-center[0])
    centered.parm("tz").set(-center[2])
    centered.parm("px").set(-center[0])
    centered.parm("pz").set(-center[2])


    #connect grey shader
    material = sweep_geo.createNode("material", "material")
    material.setInput(0, centered)
    material.parm("shop_materialpath1").set("/obj/lookdev_sweep/matnet/grey_shader")

    #set display flags and null output
    output = sweep_geo.createNode("null", "OUT")
    output.setInput(0, material)
    output.setDisplayFlag(True)
    output.setRenderFlag(True)
    
    #create matnet and dark grey shader inside network
    matnet = sweep_geo.createNode("matnet", "matnet")
    shader = matnet.createNode("principledshader", "grey_shader")
    shader.parmTuple("basecolor").set((0.007, 0.007, 0.007))
    shader.parm("rough").set(0.5)
    matnet.layoutChildren()

    sweep_geo.layoutChildren()
    return sweep_geo


### create lookdev ref geo (chrome ball, grey ball, and macbeth color chart) 
def create_lookdev_reference_kit(parent_node, center, size, texture_path, cam_distance):
    refs_geo = parent_node.createNode("geo", "lookdev_refs")
    for child in refs_geo.children():
        child.destroy()

    spacing = 2.5 #space between chart and balls
    ball_radius = 1

    # Chrome Ball
    chrome = refs_geo.createNode("sphere", "chrome_ball")
    chrome.parm("type").set(2)
    chrome.parmTuple("t").set((-spacing, 0, 0))

    chrome_mat = refs_geo.createNode("material", "chrome_mat")
    chrome_mat.setInput(0, chrome)
    chrome_mat.parm("shop_materialpath1").set("/obj/lookdev_refs/matnet/chrome_shader")

    # Grey Ball 
    grey = refs_geo.createNode("sphere", "grey_ball")
    grey.parm("type").set(2)
    grey.parmTuple("t").set((spacing, 0, 0))

    grey_mat = refs_geo.createNode("material", "grey_mat")
    grey_mat.setInput(0, grey)
    grey_mat.parm("shop_materialpath1").set("/obj/lookdev_refs/matnet/grey_shader")

    # Macbeth Chart
    chart = refs_geo.createNode("grid", "macbeth_chart")
    chart.parm("sizex").set(2)
    chart.parm("sizey").set(1.4)
    chart.parmTuple("t").set((0, (0), 0))
    chart.parmTuple("r").set((-90, 0, 0))
    
    #UV projection node setup for macbeth chart
    uv = refs_geo.createNode("uvproject", "uv")
    uv.setInput(0, chart)
    uv.parm("projtype").set(0)  #orthographic type

    #Get bounding box info from the chart geo
    refs_geo.layoutChildren() 
    chart_geo = chart.geometry()
    bbox = chart_geo.boundingBox()
    center = bbox.center()
    size = bbox.sizevec()
    
    #calculate UVs
    uv.parmTuple("t").set((center[0], center[1], center[2]))
    uv.parmTuple("s").set((size[0], size[1], size[2]))

    #macbeth chart shader connection
    chart_mat = refs_geo.createNode("material", "chart_mat")
    chart_mat.setInput(0, uv)
    chart_mat.parm("shop_materialpath1").set("/obj/lookdev_refs/matnet/macbeth_shader")
    
    #conbine chart and balls nodes with merge
    merge_refs = refs_geo.createNode("merge", "merge_refs")
    merge_refs.setNextInput(chart_mat)
    merge_refs.setNextInput(grey_mat)
    merge_refs.setNextInput(chrome_mat)
    
    #scale the lookdev refs down  
    rescale = refs_geo.createNode("xform", "scale")
    rescale.setInput(0, merge_refs)
    rescale.parmTuple("s").set((.008, .008, .008))

    #setup output and display flag
    output = refs_geo.createNode("null", "OUT")
    output.setInput(0, rescale)
    output.setDisplayFlag(True)
    output.setRenderFlag(True)

    #create material network and shaders for balls and chart
    matnet = refs_geo.createNode("matnet", "matnet")
    chrome_shader = matnet.createNode("principledshader", "chrome_shader")
    chrome_shader.parm("metallic").set(1)
    chrome_shader.parm("rough").set(0.02)

    grey_shader = matnet.createNode("principledshader", "grey_shader")
    grey_shader.parmTuple("basecolor").set((0.18, 0.18, 0.18))
    grey_shader.parm("rough").set(0.5)

    macbeth_shader = matnet.createNode("principledshader", "macbeth_shader")
    macbeth_shader.parm("basecolor_useTexture").set(True)
    macbeth_shader.parm("basecolor_texture").set(texture_path)
    macbeth_shader.parm("rough").set(1)
    macbeth_shader.parmTuple("basecolor").set((1, 1, 1))

    #layout and return 
    matnet.layoutChildren()
    refs_geo.layoutChildren()
    return refs_geo
    
    
    
def add_parameters_to_control(rig, values):

    # Create a new parameter group from the existing one
    parm_group = rig.parmTemplateGroup()
    
    # Create float parameter templates for the offsets
    hdri_rot_offset_parm = hou.FloatParmTemplate(
        name="hdri_rotation_offset", 
        label="HDRI Rotation Offset", 
        num_components=1, 
        default_value=(values["hdri_rotation_offset"],),
        min=-360, 
        max=360
    )
    
    camera_angle_offset_parm = hou.FloatParmTemplate(
        name="camera_height_offset", 
        label="Camera Height Offset", 
        num_components=1, 
        default_value=(0,),
        min=-10, 
        max= 50
    )
    
    
    # Apply to the node
    rig.setParmTemplateGroup(parm_group)
        
    #add parameters into transform group
    for entry in parm_group.entries():
        if isinstance(entry, hou.FolderParmTemplate) and entry.label() == "Transform":
            children = list(entry.parmTemplates())
            children.append(hdri_rot_offset_parm)
            children.append(camera_angle_offset_parm)
            updated_folder = hou.FolderParmTemplate(
                entry.name(), entry.label(), children, folder_type=entry.folderType()
            )
            parm_group.replace(entry.name(), updated_folder)
            break
    
    #hide extra parameters
    parms_to_hide = ["t", "r", "s", "p", "pr", "xOrd", "rOrd", "scale", "pre_xform", "keeppos", "childcomp", "constraints_on"]
    for parm in parms_to_hide:
        parm_group.hide(parm, True)
        
              

    
    #connect param updates to node
    rig.setParmTemplateGroup(parm_group)
   
    #connect to HDRI transform relative references 
    hdri_subnet = hou.node( "/obj/lookdev_rig/hdri_rotation") 
    hdri_subnet.parm("ry").setExpression('ch("../../lookdev_rig_control/hdri_rotation_offset")', hou.exprLanguage.Hscript)  
    
    cam_angle_subnet = hou.node( "/obj/lookdev_rig/camera_transform")
    cam_angle_subnet.parm("ty").setExpression('ch("../../lookdev_rig_control/camera_height_offset")', hou.exprLanguage.Hscript)

    
    
##################################################    
### main function for building the lookdev rig ###
##################################################


def create_lookdev_envlight_rig_with_ui():
    #summon UI
    dialog = LookdevRigUI(hou.ui.mainQtWindow())
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return

    #get and check values from UI
    values = dialog.get_values()
    hdri_path = values["hdri_path"] 
    start_frame = values["start_frame"]
    
    if not os.path.isfile(hdri_path):
        hou.ui.displayMessage("Invalid HDRI path.")
        return

    # make sure object is selected before running code
    selected = hou.selectedNodes()
    if not selected:
        hou.ui.displayMessage("Please select a geometry node.")
        return
        
    #get info from object bounding box 
    geo = selected[0].displayNode().geometry()
    object = selected[0]
    object_path = object.path()
    bbox = geo.boundingBox()
    center = bbox.center()
    size = bbox.sizevec()
    
    #change distance increment depending on wide vs narrow object
    if size[0] > size[1]:
        dist_inc = 2.5
    else:
        dist_inc = 3
    cam_distance = max(size) * dist_inc #calculate distance from camera to object
    obj = hou.node("/obj")

    #create null that controls angle shift of camera 
    rig = obj.createNode("null", "lookdev_rig_control")
    rig.parm("controltype").set(1)
    rig.setColor(hou.Color((0, 1, 0)))
    rig.setUserData("nodeshape", "star")
    

    #create the lookdev camera
    cam = obj.createNode("cam", "lookdev_cam")
    cam_null = obj.createNode("null", "camera_transform")
    cam_null.setDisplayFlag(False)
    cam_null.setColor(hou.Color((1, 0, 0)))
    cam.setFirstInput(cam_null)

    #create null that controls animation of sweep geo
    sweep_null = obj.createNode("null", "sweep_animation")
    sweep_null.setDisplayFlag(False)
    sweep_null.setColor(hou.Color((1, 0, 0)))
  
    #call functions that setup the camera and sweep animations
    update_camera_animation(cam, center, cam_distance, values["rotation_offset"], start_frame)
    update_sweep_animation(sweep_null, center, cam_distance, values["rotation_offset"], start_frame)

    #place null at object location for orientation
    lookat = obj.createNode("null", "lookat_target")
    lookat.parmTuple("t").set(center)
    for parm_name in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]: 
        lookat.parm(parm_name).lock(True)
    lookat.setDisplayFlag(False)
    lookat.setColor(hou.Color((1, 0, 0)))
    
    #create nulls to direct camera and sweep angles
    cam.parm("lookatpath").set(lookat.path())
    sweep_null.parm("lookatpath").set(lookat.path())

    #create HDRI light and setup settings
    env = obj.createNode("envlight", "lookdev_envlight")
    env.parm("light_enable").set(True)
    env.parm("light_intensity").set(1.0)
    env.parm("light_contribprimary").set(True)
    env.parm("env_map").set(hdri_path)
    update_envlight_animation(env, values["rotation_offset"], values["hdri_rotation_offset"], start_frame)

    
    #create null that controls rotation offset of HDRI
    hdri_null = obj.createNode("null", "hdri_rotation")
    hdri_null.setDisplayFlag(False)
    hdri_null.setColor(hou.Color((1, 0, 0)))
    env.setFirstInput(hdri_null)
   
    
    #create and transform sweep geo if requested in UI
    if values["sweep_enabled"]:
        sweep = create_sweep(size, center, cam_distance)
        sweep.setFirstInput(sweep_null)
        sweep.parm("tz").set(-cam_distance)
        sweep.parm("ty").set(-(center[1]))
        sweep.parm("tx").set((center[0]))
        for parm_name in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]: 
            sweep.parm(parm_name).lock(True)
    else:
        sweep = hou.node("/obj").createNode("geo", "lookdev_sweep")
     
             

    if values["add_refkit"]:
        lookdev_refs = create_lookdev_reference_kit(obj, center, size, values["macbeth_path"], cam_distance)
        #update_lookdev_refs_animation(values["rotation_offset"])
        lookdev_refs.setFirstInput(cam) #orient towards camera transform
        
        #calculate location of reference geo - arbitrary numbers for upper left corner of 16:9 camera (so uh please don't change the aspect ratio..)
        lookdev_refs.parm("tz").set(-.25)
        lookdev_refs.parm("ty").set(.047)
        lookdev_refs.parm("tx").set(-.072)
        for parm_name in ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]: 
            lookdev_refs.parm(parm_name).lock(True)
    else:
        lookdev_refs = hou.node("/obj").createNode("geo", "lookdev_refs")
        
        
   #create mantra rop and add objects     
    ropnet = obj.createNode("ropnet", "lookdev_ropnet")
    mantra = ropnet.createNode("ifd", "lookdev_mantra")
    mantra.parm("camera").set(cam.path())
    mantra.parm("vobject").set("")
    mantra.parm("forceobject").set(lookdev_refs.path() + " " + sweep.path() + " " + object_path)
    mantra.parm("alights").set("")
    mantra.parm("forcelights").set(env.path())
    

    
    #put nodes into a new subnet
    nodes_to_move = [cam, lookdev_refs, sweep, env, lookat, sweep_null, cam_null, hdri_null]
    subnet = obj.createNode("subnet", "lookdev_rig")
    hou.moveNodesTo(nodes_to_move, subnet)
    subnet.setColor(hou.Color((1, .7, .7)))
    subnet.layoutChildren()
    
    
    #call function to add parameters to control null
    add_parameters_to_control(rig, values)
    
    #create a network box for the obj level lookdev rig nodes
    network_box = obj.createNetworkBox()
    nodes_to_group = [subnet, rig, ropnet]
    obj.layoutChildren(items = nodes_to_group) 
    for node in nodes_to_group: 
        network_box.addItem(node) 
    network_box.fitAroundContents() 
    
    #layout ropnet nodes
    ropnet.layoutChildren()

    #navigate back to obj level
    hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor).setPwd(hou.node("/obj"))

    # Save settings for next time
    save_settings(values)

create_lookdev_envlight_rig_with_ui()
