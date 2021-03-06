import bpy
import globs
import tools.common
import tools.supporter

from ui.main import ToolPanel

from tools import eyetracking

from tools.register import register_wrap
from tools.common import version_2_79_or_older


@register_wrap
class EyeTrackingPanel(ToolPanel, bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_eye_v3'
    bl_label = 'Eye Tracking'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        row = col.row(align=True)
        row.prop(context.scene, 'eye_mode', expand=True)

        if context.scene.eye_mode == 'CREATION':

            mesh_count = len(tools.common.get_meshes_objects(check=False))
            if mesh_count == 0:
                col.separator()
                row = col.row(align=True)
                row.scale_y = 1.1
                row.label(text='No meshes found!', icon='ERROR')
            elif mesh_count > 1:
                col.separator()
                row = col.row(align=True)
                row.scale_y = 1.1
                row.prop(context.scene, 'mesh_name_eye', icon='MESH_DATA')

            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.1
            row.prop(context.scene, 'head', icon='BONE_DATA')
            row = col.row(align=True)
            row.scale_y = 1.1
            if context.scene.disable_eye_movement:
                row.active = False
            row.prop(context.scene, 'eye_left', icon='BONE_DATA')
            row = col.row(align=True)
            row.scale_y = 1.1
            if context.scene.disable_eye_movement:
                row.active = False
            row.prop(context.scene, 'eye_right', icon='BONE_DATA')

            col.separator()
            row = col.row(align=True)
            row.scale_y = 1.1
            if context.scene.disable_eye_blinking:
                row.active = False
            row.prop(context.scene, 'wink_left', icon='SHAPEKEY_DATA')
            row = col.row(align=True)
            row.scale_y = 1.1
            if context.scene.disable_eye_blinking:
                row.active = False
            row.prop(context.scene, 'wink_right', icon='SHAPEKEY_DATA')
            row = col.row(align=True)
            row.scale_y = 1.1
            if context.scene.disable_eye_blinking:
                row.active = False
            row.prop(context.scene, 'lowerlid_left', icon='SHAPEKEY_DATA')
            row = col.row(align=True)
            row.scale_y = 1.1
            if context.scene.disable_eye_blinking:
                row.active = False
            row.prop(context.scene, 'lowerlid_right', icon='SHAPEKEY_DATA')

            col.separator()
            row = col.row(align=True)
            row.prop(context.scene, 'disable_eye_blinking')

            row = col.row(align=True)
            row.prop(context.scene, 'disable_eye_movement')

            if not context.scene.disable_eye_movement:
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'eye_distance')

            col = box.column(align=True)
            row = col.row(align=True)
            row.operator(eyetracking.CreateEyesButton.bl_idname, icon='TRIA_RIGHT')

            # armature = common.get_armature()
            # if "RightEye" in armature.pose.bones:
            #     row = col.row(align=True)
            #     row.label(text='Eye Bone Tweaking:')
        else:
            armature = tools.common.get_armature()
            if not armature:
                box.label(text='No model found!', icon='ERROR')
                return

            if bpy.context.active_object is not None and bpy.context.active_object.mode != 'POSE':
                col.separator()
                row = col.row(align=True)
                row.scale_y = 1.5
                row.operator(eyetracking.StartTestingButton.bl_idname, icon='TRIA_RIGHT')
            else:
                # col.separator()
                # row = col.row(align=True)
                # row.operator('eyes.test_stop', icon='PAUSE')

                col.separator()
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'eye_rotation_x', icon='FILE_PARENT')
                row = col.row(align=True)
                row.prop(context.scene, 'eye_rotation_y', icon='ARROW_LEFTRIGHT')
                row = col.row(align=True)
                row.operator(eyetracking.ResetRotationButton.bl_idname, icon=globs.ICON_EYE_ROTATION)

                # global slider_z
                # if context.scene.eye_blink_shape != slider_z:
                #     slider_z = context.scene.eye_blink_shape
                #     eyetracking.update_bones(context, slider_z)

                col.separator()
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'eye_distance')
                row = col.row(align=True)
                row.operator(eyetracking.AdjustEyesButton.bl_idname, icon='CURVE_NCIRCLE')

                col.separator()
                col.separator()
                row = col.row(align=True)
                row.prop(context.scene, 'eye_blink_shape')
                row.operator(eyetracking.TestBlinking.bl_idname, icon='RESTRICT_VIEW_OFF')
                row = col.row(align=True)
                row.prop(context.scene, 'eye_lowerlid_shape')
                row.operator(eyetracking.TestLowerlid.bl_idname, icon='RESTRICT_VIEW_OFF')
                row = col.row(align=True)
                row.operator(eyetracking.ResetBlinkTest.bl_idname, icon='FILE_REFRESH')

                if armature.name != 'Armature':
                    col.separator()
                    col.separator()
                    col.separator()
                    row = col.row(align=True)
                    row.scale_y = 0.3
                    row.label(text="Your armature has to be named 'Armature'", icon='ERROR')
                    row = col.row(align=True)
                    row.label(text="      for Eye Tracking to work!")
                    row = col.row(align=True)
                    row.scale_y = 0.3
                    row.label(text="      (currently '" + armature.name + "')")

                if context.scene.mesh_name_eye != 'Body':
                    col.separator()
                    col.separator()
                    col.separator()
                    row = col.row(align=True)
                    row.scale_y = 0.3
                    row.label(text="The mesh containing the eyes has to be", icon='ERROR')
                    row = col.row(align=True)
                    row.label(text="      named 'Body' for Eye Tracking to work!")
                    row = col.row(align=True)
                    row.scale_y = 0.3
                    row.label(text="      (currently '" + context.scene.mesh_name_eye + "')")

                col.separator()
                col.separator()
                col.separator()
                row = col.row(align=True)
                row.scale_y = 0.3
                row.label(text="Don't forget to assign 'LeftEye' and 'RightEye'", icon='INFO')
                row = col.row(align=True)
                row.label(text="      to the eyes in Unity!")

                row = col.row(align=True)
                row.scale_y = 1.5
                row.operator(eyetracking.StopTestingButton.bl_idname, icon='PAUSE')
