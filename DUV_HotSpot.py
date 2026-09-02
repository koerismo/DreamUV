from math import inf
from typing import TYPE_CHECKING

from bmesh.types import BMFace
import bpy
import bmesh
import random
from mathutils import Vector
from . import DUV_Utils
from bpy.props import EnumProperty, BoolProperty, StringProperty, FloatProperty, IntProperty

if TYPE_CHECKING:
    import hotspotter_core as hsc
else:
    from . import cpp as hsc

def main(context: bpy.types.Context):
    #Check if an atlas object exists
    if context.scene.subrect_atlas is None:
        print("DreamUV: No valid atlas selected!")
        return {'FINISHED'}

    #FIX: make sure we actually have a valid active MESH object before doing
    #anything else. Without this check, if the active object is missing or
    #isn't a mesh (e.g. an empty/atlas reference object got left active),
    #editmode_toggle()/mode_set() below fail with "poll() failed, context is incorrect".
    active_obj: bpy.types.Object | None = bpy.context.view_layer.objects.active
    if active_obj is None or active_obj.type != 'MESH':
        print("DreamUV: No valid active mesh object selected, aborting HotSpot.")
        return {'CANCELLED'}

    #make sure active object is actually selected in edit mode:
    if active_obj.mode == 'EDIT':
        active_obj.select_set(True)
    
        
    #check for object or edit mode:
    is_object_mode = False
    if active_obj.mode == 'OBJECT':
        is_object_mode = True
        #switch to edit and select all
        #FIX: use mode_set(mode='EDIT') with an explicit context override instead of
        #editmode_toggle(). mode_set() only requires an active object to pass its
        #poll check, which we've now guaranteed above, making this far more reliable
        #than editmode_toggle() when called from a UI button.
        with bpy.context.temp_override(active_object=active_obj, object=active_obj):
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

    #check if uv sync selection is used and turn off if so
    use_uv_sync = False
    if bpy.context.scene.tool_settings.use_uv_select_sync == True:
        use_uv_sync = True
        bpy.context.scene.tool_settings.use_uv_select_sync = False


    active_object: bpy.types.Object = bpy.context.view_layer.objects.active

    assert isinstance(active_object.data, bpy.types.Mesh), "DreamUV: Active object must be a mesh!"
    bm = bmesh.from_edit_mesh(active_object.data)

    #ADD MATERIAL
    if context.scene.duv_hotspotmaterial is not None:
        mat_index = 0
        mat_exists = False
        for slot in active_object.data.materials:
            if slot == context.scene.duv_hotspotmaterial:
                mat_exists = True
                break
            mat_index += 1
        
        if mat_exists is False:
            active_object.data.materials.append(context.scene.duv_hotspotmaterial)
        
        for face in bm.faces:
            if face.select: 
                face.material_index = mat_index
    
    bmesh.update_edit_mesh(active_object.data)

    #CREATE WORKING DUPLICATE!
    object_original: bpy.types.Object = bpy.context.view_layer.objects.active
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.duplicate()
    
    #setup hard edges on duplicate 
    #create hard edges 
    
    assert bpy.context.active_object, "DreamUV: Duplicated object was not made active!"

    #bpy.ops.object.shade_smooth_by_angle()
    use_smooth_modifier = False
    for slot in bpy.context.active_object.modifiers:
        if slot.name == 'Auto Smooth' or slot.name == 'Smooth by Angle':
            use_smooth_modifier = True
    
    if use_smooth_modifier:
        #apply smoothing modifier
        bpy.ops.object.modifier_apply(modifier="Smooth by Angle")
    else:
        #auto smooth - assume 30 degrees until someone complains
        bpy.ops.object.shade_smooth_by_angle(angle=0.523599)
    
    bpy.ops.object.editmode_toggle()
    bpy.context.view_layer.objects.active.name = "dreamuv_temp"
    object_temporary = bpy.context.view_layer.objects.active

    #PREPROCESS - save seams and hard edges
    active_object = bpy.context.view_layer.objects.active
    assert isinstance(active_object.data, bpy.types.Mesh), "DreamUV: Active object must be a mesh!"

    bm = bmesh.from_edit_mesh(active_object.data)

    selected_faces: list[BMFace] = list()
    for face in bm.faces:
        if face.select:
            selected_faces.append(face)

    bmesh.update_edit_mesh(active_object.data)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    
    #broken in 4.1
    #angle = bpy.context.object.data.auto_smooth_angle
    #bpy.ops.mesh.edges_select_sharp(sharpness=angle)

    
    bpy.ops.mesh.mark_seam(clear=False)
    bpy.ops.mesh.select_all(action='DESELECT')

    for edge in bm.edges:
        if edge.seam or edge.smooth == False:
            edge.select = True

    bpy.ops.mesh.edge_split(type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')


    #select all faces to be hotspotted again:
    
    for face in selected_faces:
        face.select = True

    #PREPROCESS - find islands

    #create UV islands using blender unwrap
    bpy.ops.uv.unwrap(method='CONFORMAL', margin=1.0)
    #list islands
    #iterate using select linked uv

    islands: list[list[BMFace]] = list()        
    temp_faces: list[BMFace] = list()
    updated_faces: list[BMFace] = list()
    #MAKE FACE LIST

    for face in bm.faces:
        if face.select:
            updated_faces.append(face)
            temp_faces.append(face)
            face.select = False

    while len(temp_faces) > 0:
        updated_faces[0].select = True
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_linked(delimit={'UV'})

        island_faces: list[BMFace] = list()
        for face in bm.faces:
            if face.select:
                island_faces.append(face)
        islands.append(island_faces)

        #create updated list
        temp_faces.clear()
        for face in updated_faces:
            if face.select == False:
                temp_faces.append(face)
            else:
                face.select = False 
        
        #make new list into updated list
        updated_faces.clear()
        updated_faces = temp_faces.copy()

    bpy.ops.uv.select_all(action='SELECT')

    #get atlas
    atlas = DUV_Utils.read_atlas(context)

    #NOW ITERATE!
    for island in islands:
        uv_layer = bm.loops.layers.uv.verify()

        for face in selected_faces:
            face.select = False
        
        for face in island:
            face.select = True
                    
        island_faces: list[BMFace] = list()
        
        #MAKE FACE LIST
        for face in bm.faces:
            if face.select:
                island_faces.append(face)    

        #get original size
        xmin2, xmax2 = island_faces[0].loops[0][uv_layer].uv.x, island_faces[0].loops[0][uv_layer].uv.x
        ymin2, ymax2 = island_faces[0].loops[0][uv_layer].uv.y, island_faces[0].loops[0][uv_layer].uv.y
        for face in island_faces: 
            for vert in face.loops:
                xmin2 = min(xmin2, vert[uv_layer].uv.x)
                xmax2 = max(xmax2, vert[uv_layer].uv.x)
                ymin2 = min(ymin2, vert[uv_layer].uv.y)
                ymax2 = max(ymax2, vert[uv_layer].uv.y)
      
        #try fitting selection to square
        is_rect = DUV_Utils.square_fit(context)
        if is_rect is False:
            #return {'FINISHED'}
        
            bmesh.update_edit_mesh(active_object.data)
            bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
            uv_layer = bm.loops.layers.uv.verify()

        #rotate to world angle here:
        DUV_Utils.get_orientation(context)

        #FIT TO 0-1 range
        if len(island_faces):
            xmin, ymin = inf, inf
            xmax, ymax = -inf, -inf
            for face in island_faces: 
                for vert in face.loops:
                    xmin = min(xmin, vert[uv_layer].uv.x)
                    xmax = max(xmax, vert[uv_layer].uv.x)
                    ymin = min(ymin, vert[uv_layer].uv.y)
                    ymax = max(ymax, vert[uv_layer].uv.y)
        else:
            xmin, ymin = 0, 0
            xmax, ymax = 1, 1

        #prevent divide by 0:
        if (xmax - xmin) == 0:
            xmin = .1
        if (ymax - ymin) == 0:
            ymin = .1

        edge_x = xmax - xmin
        edge_y = ymax - ymin

        for face in island_faces:
            for loop in face.loops:
                loop[uv_layer].uv.x -= xmin
                loop[uv_layer].uv.y -= ymin
                loop[uv_layer].uv.x /= edge_x
                loop[uv_layer].uv.y /= edge_y

        island_aspect = edge_x / edge_y
        island_area: float = sum(f.calc_area() for f in island_faces if f.select)
        
        if is_rect is False:
            #calulate ratio empty vs full
            size_ratio = DUV_Utils.get_uv_ratio(context)
            #prevent divide by 0:
            if size_ratio == 0:
                size_ratio = 1.0
            island_area = island_area / size_ratio

        if island_aspect > 1:
            island_aspect = round(island_aspect)
        else: 
            if island_aspect > 0.0001: #prevent divide by 0
                island_aspect = 1/(round(1/island_aspect))

        #ASPECT LOWER THAN 1.0 = TALL
        #ASPECT HIGHER THAN 1.0 = WIDE

        #find closest aspect ratio in list

        #2 variations depending on tall or wide

        index = 0
        temp_length = abs(atlas[0].pos_aspect - island_aspect)
        temp_index = 0

        use_world_orientation = context.scene.duv_useorientation

        if use_world_orientation:
            for number in atlas:
                    test_length = abs(number.aspect-island_aspect) 
                    if test_length < temp_length:
                        temp_length = test_length
                        temp_index = index
                    index += 1

        if not use_world_orientation:
            #wide:
            if island_aspect >= 1.0:
                for number in atlas:
                    test_length = abs(number.pos_aspect-island_aspect) 
                    if test_length < temp_length:
                        temp_length = test_length
                        temp_index = index
                    index += 1

            #tall:
            else:
                temp_length = abs((atlas[0].pos_aspect)-(1/island_aspect))
                for number in atlas:
                    test_length = abs((number.pos_aspect)-(1/island_aspect)) 
                    if test_length < temp_length:
                        temp_length = test_length
                        temp_index = index
                    index += 1

        #NOW MAKE LIST OF ASPECTS!
        aspect_bucket = list()

        for r in atlas:
            if r.aspect == atlas[temp_index].aspect:
                aspect_bucket.append(r)
            if use_world_orientation is False:
                if r.aspect == 1 / atlas[temp_index].aspect:
                    aspect_bucket.append(r)

        #find closest size in bucket:
        index = 0

        temp_length = abs(aspect_bucket[0].size - island_area)
        temp_index = 0

        valid_rects = list()
        for a in aspect_bucket:
            test_length = abs(a.size-island_area) 
            if test_length <= temp_length:
                temp_length = test_length
                temp_index = index
            index += 1
        
        index = 0
        for a in aspect_bucket:
            if a.size == aspect_bucket[temp_index].size:
                valid_rects.append(index)
            index += 1

        temp_index = random.choice(valid_rects)

        #test if coords are already asigned by comparing minmaxes, then try again

        #2 assign uv
        #get minmax of target rect
        xmin, xmax = aspect_bucket[temp_index].uvcoord[0].x, aspect_bucket[temp_index].uvcoord[0].x
        ymin, ymax = aspect_bucket[temp_index].uvcoord[0].y, aspect_bucket[temp_index].uvcoord[0].y

        for vert in aspect_bucket[temp_index].uvcoord:
            xmin = min(xmin, vert.x)
            xmax = max(xmax, vert.x)
            ymin = min(ymin, vert.y)
            ymax = max(ymax, vert.y)

        #flip if aspect is inverted

        if xmin == xmin2 and ymin == ymin2 and xmax == xmax2 and ymax == ymax2 and len(valid_rects) > 1:
            #remove current choice
            valid_rects.remove(temp_index)
            #print(validrects)

            temp_index = random.choice(valid_rects)

            xmin, xmax = aspect_bucket[temp_index].uvcoord[0].x, aspect_bucket[temp_index].uvcoord[0].x
            ymin, ymax = aspect_bucket[temp_index].uvcoord[0].y, aspect_bucket[temp_index].uvcoord[0].y

            for vert in aspect_bucket[temp_index].uvcoord:
                xmin = min(xmin, vert.x)
                xmax = max(xmax, vert.x)
                ymin = min(ymin, vert.y)
                ymax = max(ymax, vert.y)

        #flip U and V if aspect is reversed:
        #WIDE case becomes TALL
        if aspect_bucket[temp_index].aspect < 1.0 and island_aspect >= 1.0:
            for face in island_faces:
                for loop in face.loops:
                    newx = loop[uv_layer].uv.y
                    newy = loop[uv_layer].uv.x
                    loop[uv_layer].uv.x = newx
                    loop[uv_layer].uv.y = newy
        
        #TALL case becomes WIDE
        if aspect_bucket[temp_index].aspect > 1.0 and island_aspect < 1.0:
            for face in island_faces:
                for loop in face.loops:
                    newx = loop[uv_layer].uv.y
                    newy = loop[uv_layer].uv.x
                    loop[uv_layer].uv.x = newx
                    loop[uv_layer].uv.y = newy

        #check if uv needs to be inset
        if context.scene.duv_hotspotuseinset is True:
            pixel_inset = context.scene.hotspotinsetpixels / context.scene.hotspotinsettexsize
            xmin += pixel_inset
            xmax -= pixel_inset
            ymin += pixel_inset
            ymax -= pixel_inset

        #apply the new UV
        for face in island_faces:
            for loop in face.loops:
                loop[uv_layer].uv.x *= xmax-xmin
                loop[uv_layer].uv.y *= ymax-ymin
                loop[uv_layer].uv.x += xmin
                loop[uv_layer].uv.y += ymin

        use_world_orientation = context.scene.duv_useorientation
        use_mirrorx = context.scene.duv_usemirrorx
        use_mirrory = context.scene.duv_usemirrory

        #MIRRORING:

        if use_world_orientation is False:
            #flip around square aspects randomly
            if island_aspect == 1:
                flips = random.randint(0, 3)
                for x in range(flips):
                    bpy.ops.view3d.dreamuv_uvcycle()
        
        #and also do randomized mirroring:
        if use_mirrorx is True:
            randomMirrorX = random.randint(0, 1)
            if randomMirrorX == 1:
                bpy.ops.view3d.dreamuv_uvmirror(direction = "x")

        if use_mirrory is True:
            randomMirrorY = random.randint(0, 1)
            if randomMirrorY == 1:
                bpy.ops.view3d.dreamuv_uvmirror(direction = "y")

        #apply material from index
        if context.scene.duv_hotspotmaterial is not None:
            for face in island_faces:   
                face.material_index = mat_index

    for face in selected_faces:
        face.select = True
    bmesh.update_edit_mesh(active_object.data)
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    #transfer UV maps back to original mesh
    
    active_object = bpy.context.view_layer.objects.active
    bm = bmesh.from_edit_mesh(active_object.data) 
    uv_layer = bm.loops.layers.uv.verify()
    uv_backup = list();
    #print("new UV:")
    for face in bm.faces:
        backupface = list()
        for vert in face.loops:
            backupuv = list()
            backupuv.append(vert[uv_layer].uv.x)
            backupuv.append(vert[uv_layer].uv.y)
            backupface.append(backupuv)
            #print(backupuv)
        uv_backup.append(backupface)
        
    #now apply to original mesh
    bpy.ops.object.editmode_toggle()
    object_temporary.select_set(False)
    object_original.select_set(True)
    bpy.ops.object.editmode_toggle()
    
    active_object = object_original
    bm = bmesh.from_edit_mesh(active_object.data) 
    uv_layer = bm.loops.layers.uv.verify()
    #uv_backup = list();
    #print("new UV:")
    for face, backupface in zip(bm.faces, uv_backup):
        for vert, backupuv in zip(face.loops, backupface):
            vert[uv_layer].uv.x = backupuv[0]
            vert[uv_layer].uv.y = backupuv[1]
    bmesh.update_edit_mesh(active_object.data)
    
           
    
    bpy.ops.object.editmode_toggle() 
    
    object_original.select_set(False)
    object_temporary.select_set(True)
    bpy.ops.object.delete(use_global=False)
    object_original.select_set(True)
    context.view_layer.objects.active=bpy.context.selected_objects[0]
    
    if use_uv_sync == True:
        bpy.ops.object.editmode_toggle()
        bpy.context.scene.tool_settings.use_uv_select_sync = True
        bpy.ops.object.editmode_toggle()
        
    
    if is_object_mode is False:
        bpy.ops.object.editmode_toggle() 
    
    #temp - do both uvs!
    #if context.scene.duv_uv2copy == True:
    #    if bpy.context.object.mode == 'EDIT':
    #        bpy.ops.brm.copyuvs()
    #        print("copying uvs")
        
class DREAMUV_OT_hotspotter(bpy.types.Operator):
    """Unwrap selection using the atlas object as a guide"""
    bl_idname = "view3d.dreamuv_hotspotter"
    bl_label = "HotSpot"
    bl_options = {"UNDO"}

    def execute(self, context):
    
        #make sure selection is active:
        if context.scene.duv_hotspot_atlas1 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas1
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial1
        if context.scene.duv_hotspot_atlas2 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas2
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial2    
        if context.scene.duv_hotspot_atlas3 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas3
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial3
        if context.scene.duv_hotspot_atlas4 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas4
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial4
        if context.scene.duv_hotspot_atlas5 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas5
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial5
        if context.scene.duv_hotspot_atlas6 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas6
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial6
        if context.scene.duv_hotspot_atlas7 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas7
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial7
        if context.scene.duv_hotspot_atlas8 == True:
            context.scene.subrect_atlas = context.scene.subrect_atlas8
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial8
        
        
        #remember selected uv
        uv_index = bpy.context.view_layer.objects.active.data.uv_layers.active_index
        if context.scene.duv_hotspot_uv1 == True:
            bpy.context.view_layer.objects.active.data.uv_layers.active_index = 0
            main(context)
        if context.scene.duv_hotspot_uv2 == True:
            bpy.context.view_layer.objects.active.data.uv_layers.active_index = 1
            main(context)
        if context.scene.duv_hotspot_uv1 == False and context.scene.duv_hotspot_uv2 == False:
            #just uv selected uv
            main(context)
        #reset selected uv
        bpy.context.view_layer.objects.active.data.uv_layers.active_index = uv_index
        
        if context.scene.duv_autoboxmap == True:
            bpy.ops.view3d.dreamuv_uvboxmap()
        
        #main(context)
        return {'FINISHED'}
        
        bpy.ops.object.editmode_toggle() 
        
class DREAMUV_OT_pushhotspot(bpy.types.Operator):
    """Set hotspot settings from list"""
    bl_idname = "view3d.dreamuv_pushhotspot"
    bl_label = "Push HotSpot"
    bl_options = {"UNDO"}

    index : bpy.props.IntProperty()

    def execute(self, context):
        
        context.scene.duv_hotspot_atlas1 = False
        context.scene.duv_hotspot_atlas2 = False
        context.scene.duv_hotspot_atlas3 = False
        context.scene.duv_hotspot_atlas4 = False
        context.scene.duv_hotspot_atlas5 = False
        context.scene.duv_hotspot_atlas6 = False
        context.scene.duv_hotspot_atlas7 = False
        context.scene.duv_hotspot_atlas8 = False
    
        if self.index == 1:
            context.scene.subrect_atlas = context.scene.subrect_atlas1
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial1
            context.scene.duv_hotspot_atlas1 = True
        if self.index == 2:
            context.scene.subrect_atlas = context.scene.subrect_atlas2
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial2
            context.scene.duv_hotspot_atlas2 = True
        if self.index == 3:
            context.scene.subrect_atlas = context.scene.subrect_atlas3
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial3
            context.scene.duv_hotspot_atlas3 = True
        if self.index == 4:
            context.scene.subrect_atlas = context.scene.subrect_atlas4
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial4
            context.scene.duv_hotspot_atlas4 = True       
        if self.index == 5:
            context.scene.subrect_atlas = context.scene.subrect_atlas5
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial5
            context.scene.duv_hotspot_atlas5 = True
        if self.index == 6:
            context.scene.subrect_atlas = context.scene.subrect_atlas6
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial6
            context.scene.duv_hotspot_atlas6 = True
        if self.index == 7:
            context.scene.subrect_atlas = context.scene.subrect_atlas7
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial7
            context.scene.duv_hotspot_atlas7 = True
        if self.index == 8:
            context.scene.subrect_atlas = context.scene.subrect_atlas8
            context.scene.duv_hotspotmaterial = context.scene.duv_hotspotmaterial8
            context.scene.duv_hotspot_atlas8 = True
        
        return {'FINISHED'}
