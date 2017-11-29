# MIT License

# Copyright (c) 2017 GiveMeAllYourCats

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Code author: GiveMeAllYourCats
# Repo: https://github.com/michaeldegroot/cats-blender-plugin
# Edits by:

import bpy
import tools.common

from collections import OrderedDict


class AutoVisemeButton(bpy.types.Operator):
    bl_idname = 'auto.viseme'
    bl_label = 'Create visemes'
    bl_options = {'REGISTER', 'UNDO'}

    def mix_shapekey(self, context, shapes, shapekey_data, new_index, rename_to, intensity):
        mesh = bpy.data.objects[context.scene.mesh_name_viseme]

        # Remove existing shapekey
        for index, shapekey in enumerate(bpy.data.objects[context.scene.mesh_name_viseme].data.shape_keys.key_blocks):
            if shapekey.name == rename_to:
                bpy.context.active_object.active_shape_key_index = index
                bpy.ops.object.shape_key_remove()
                break

        # rename shapekey if it already exists and set value to 0
        for shapekey in mesh.data.shape_keys.key_blocks:
            shapekey.value = 0

        # Set the shape key values
        for shapekey_data_context in shapekey_data:
            selector = shapekey_data_context[0]
            shapekey_value = shapekey_data_context[1]

            for index, shapekey in enumerate(mesh.data.shape_keys.key_blocks):
                if selector == shapekey.name:
                    mesh.active_shape_key_index = index
                    shapekey.value = shapekey_value * intensity

        # Create the new shape key
        mesh.shape_key_add(name=rename_to, from_mix=True)
        bpy.ops.object.shape_key_clear()

        # Select the created shapekey
        mesh.active_shape_key_index = len(mesh.data.shape_keys.key_blocks) - 1

        # TODO: This takes too long too complete, find a alternative
        # Might be best to keep this commented as it's just for aesthetic reasons.

        # Re-adjust index position
        # position_correct = False
        # while position_correct is False:
        #     if mesh.active_shape_key_index != new_index:
        #         bpy.ops.object.shape_key_move(type='UP')
        #     else:
        #         position_correct = True

        # Reset context scenes
        context.scene.mouth_a = shapes[0]
        context.scene.mouth_o = shapes[1]
        context.scene.mouth_ch = shapes[2]

    def execute(self, context):
        # PreserveState = tools.common.PreserveState()
        # PreserveState.save()

        tools.common.unhide_all()

        tools.common.unselect_all()
        tools.common.select(bpy.data.objects[context.scene.mesh_name_viseme])
        tools.common.switch('OBJECT')

        # Rename selected shapes and rename them back at the end
        shapes = [context.scene.mouth_a, context.scene.mouth_o, context.scene.mouth_ch]
        renamed_shapes = [context.scene.mouth_a, context.scene.mouth_o, context.scene.mouth_ch]
        mesh = bpy.data.objects[context.scene.mesh_name_viseme]
        for shapekey in mesh.data.shape_keys.key_blocks:
            if shapekey.name == context.scene.mouth_a:
                print(shapekey.name + " " + context.scene.mouth_a)
                shapekey.name = shapekey.name + "_old"
                context.scene.mouth_a = shapekey.name
                renamed_shapes[0] = shapekey.name
            if shapekey.name == context.scene.mouth_o:
                print(shapekey.name + " " + context.scene.mouth_a)
                if context.scene.mouth_a != context.scene.mouth_o:
                    shapekey.name = shapekey.name + "_old"
                context.scene.mouth_o = shapekey.name
                renamed_shapes[1] = shapekey.name
            if shapekey.name == context.scene.mouth_ch:
                print(shapekey.name + " " + context.scene.mouth_a)
                if context.scene.mouth_a != context.scene.mouth_ch and context.scene.mouth_o != context.scene.mouth_ch:
                    shapekey.name = shapekey.name + "_old"
                context.scene.mouth_ch = shapekey.name
                renamed_shapes[2] = shapekey.name

        shape_a = context.scene.mouth_a
        shape_o = context.scene.mouth_o
        shape_ch = context.scene.mouth_ch

        # Set up the shape keys. Some values are made in order to keep Blender from deleting them. There should never be duplicate shape keys!
        shapekey_data = OrderedDict()
        shapekey_data['vrc.v_aa'] = {
            'index': 5,
            'mix': [
                [(shape_a), (0.9999)]
            ]
        }
        shapekey_data['vrc.v_ch'] = {
            'index': 6,
            'mix': [
                [(shape_ch), (0.9998)]
            ]
        }
        shapekey_data['vrc.v_dd'] = {
            'index': 7,
            'mix': [
                [(shape_a), (0.3)],
                [(shape_ch), (0.7)]
            ]
        }
        shapekey_data['vrc.v_e'] = {
            'index': 8,
            'mix': [
                [(shape_ch), (0.7)],
                [(shape_o), (0.3)]
            ]
        }
        shapekey_data['vrc.v_ff'] = {
            'index': 9,
            'mix': [
                [(shape_a), (0.2)],
                [(shape_ch), (0.4)]
            ]
        }
        shapekey_data['vrc.v_ih'] = {
            'index': 10,
            'mix': [
                [(shape_a), (0.5)],
                [(shape_ch), (0.2)]
            ]
        }
        shapekey_data['vrc.v_kk'] = {
            'index': 11,
            'mix': [
                [(shape_a), (0.7)],
                [(shape_ch), (0.4)]
            ]
        }
        shapekey_data['vrc.v_nn'] = {
            'index': 12,
            'mix': [
                [(shape_a), (0.2)],
                [(shape_ch), (0.7)]
            ]
        }
        shapekey_data['vrc.v_oh'] = {
            'index': 13,
            'mix': [
                [(shape_a), (0.2)],
                [(shape_o), (0.8)]
            ]
        }
        shapekey_data['vrc.v_ou'] = {
            'index': 14,
            'mix': [
                [(shape_o), (0.9997)]
            ]
        }
        shapekey_data['vrc.v_pp'] = {
            'index': 15,
            'mix': [
                [(shape_a), (0.0002)],
                [(shape_o), (0.0002)]
            ]
        }
        shapekey_data['vrc.v_rr'] = {
            'index': 16,
            'mix': [
                [(shape_ch), (0.5)],
                [(shape_o), (0.3)]
            ]
        }
        shapekey_data['vrc.v_sil'] = {
            'index': 17,
            'mix': [
                [(shape_a), (0.0001)],
                [(shape_ch), (0.0001)]
            ]
        }
        shapekey_data['vrc.v_ss'] = {
            'index': 18,
            'mix': [
                [(shape_ch), (0.8)],
            ]
        }
        shapekey_data['vrc.v_th'] = {
            'index': 19,
            'mix': [
                [(shape_a), (0.4)],
                [(shape_o), (0.15)]
            ]
        }

        # Add the shape keys
        for key in shapekey_data:
            obj = shapekey_data[key]
            self.mix_shapekey(context, renamed_shapes, obj['mix'], obj['index'], key, context.scene.shape_intensity)

        # Rename shapes back
        if shapes[0] not in mesh.data.shape_keys.key_blocks:
            shapekey = mesh.data.shape_keys.key_blocks.get(renamed_shapes[0])
            shapekey.name = shapes[0]
            if renamed_shapes[2] == renamed_shapes[0]:
                renamed_shapes[2] = shapes[0]
            if renamed_shapes[1] == renamed_shapes[0]:
                renamed_shapes[1] = shapes[0]
            renamed_shapes[0] = shapes[0]

        if shapes[1] not in mesh.data.shape_keys.key_blocks:
            shapekey = mesh.data.shape_keys.key_blocks.get(renamed_shapes[1])
            shapekey.name = shapes[1]
            if renamed_shapes[2] == renamed_shapes[1]:
                renamed_shapes[2] = shapes[1]
            renamed_shapes[1] = shapes[1]

        if shapes[2] not in mesh.data.shape_keys.key_blocks:
            shapekey = mesh.data.shape_keys.key_blocks.get(renamed_shapes[2])
            shapekey.name = shapes[2]
            renamed_shapes[2] = shapes[2]

        # Reset context scenes
        context.scene.mouth_a = renamed_shapes[0]
        context.scene.mouth_o = renamed_shapes[1]
        context.scene.mouth_ch = renamed_shapes[2]

        # Set shapekey index back to 0
        bpy.context.object.active_shape_key_index = 0

        # Remove empty objects
        tools.common.switch('EDIT')
        tools.common.remove_empty()

        # Fix armature name
        tools.common.fix_armature_name()

        # tools.common.repair_shapekeys()

        # PreserveState.load()

        self.report({'INFO'}, 'Created mouth visemes!')

        return {'FINISHED'}
