# -*- coding: utf-8 -*-

import logging
import re

import bpy
import math
import mathutils

from mmd_tools_local.core import vmd
from mmd_tools_local.core.camera import MMDCamera
from mmd_tools_local.core.lamp import MMDLamp


class _FCurve:

    def __init__(self, default_value):
        self.__default_value = default_value
        self.__fcurve = None

    def setFCurve(self, fcurve):
        assert(fcurve.is_valid and self.__fcurve is None)
        self.__fcurve = fcurve

    def frameNumbers(self):
        if self.__fcurve is None:
            return set()
        return {int(kp.co[0]+0.5) for kp in self.__fcurve.keyframe_points}

    @staticmethod
    def getVMDControlPoints(kp0, kp1):
        if kp0.interpolation == 'LINEAR':
            return ((20, 20), (107, 107))

        dx, dy = kp1.co - kp0.co
        if abs(dy) < 1e-6 or abs(dx) < 1.5:
            return ((20, 20), (107, 107))

        x1, y1 = kp0.handle_right - kp0.co
        x2, y2 = kp1.handle_left - kp0.co
        x1 = max(0, min(127, int(0.5 + x1*127.0/dx)))
        x2 = max(0, min(127, int(0.5 + x2*127.0/dx)))
        y1 = max(0, min(127, int(0.5 + y1*127.0/dy)))
        y2 = max(0, min(127, int(0.5 + y2*127.0/dy)))
        return ((x1, y1), (x2, y2))

    def sampleFrames(self, frame_numbers):
        # assume set(frame_numbers) & set(self.frameNumbers()) == set(self.frameNumbers())
        fcurve = self.__fcurve
        if fcurve is None or len(fcurve.keyframe_points) < 1: # no key frames
            for i in frame_numbers:
                yield [self.__default_value, ((20, 20), (107, 107))]
            return

        evaluate = fcurve.evaluate
        frame_iter = iter(frame_numbers)
        prev_kp = None
        prev_i = None
        for kp in sorted(fcurve.keyframe_points, key=lambda x: x.co[0]):
            i = int(kp.co[0]+0.5)
            if i == prev_i:
                prev_kp = kp
                continue
            prev_i = i
            frames = []
            while True:
                frame = next(frame_iter)
                frames.append(frame)
                if frame >= i:
                    break
            assert(len(frames) >= 1 and frames[-1] == i)
            if prev_kp is None:
                for f in frames: # starting key frames
                    yield [kp.co[1], ((20, 20), (107, 107))]
            elif len(frames) == 1:
                yield [kp.co[1], self.getVMDControlPoints(prev_kp, kp)]
            else:
                #FIXME better evaluated values and interpolations
                for f in frames:
                    yield [evaluate(f), ((20, 20), (107, 107))]
            prev_kp = kp

        for f in frame_iter: # ending key frames
            yield [prev_kp.co[1], ((20, 20), (107, 107))]


class VMDExporter:

    def __init__(self):
        self.__scale = 1
        self.__frame_start = 1
        self.__frame_end = float('inf')
        self.__bone_converter_cls = vmd.importer.BoneConverter

    def __allFrameKeys(self, curves):
        all_frames = set()
        for i in curves:
            all_frames |= i.frameNumbers()

        if len(all_frames) < 1:
            return

        frame_start = min(all_frames)
        if frame_start < self.__frame_start:
            frame_start = self.__frame_start
            all_frames.add(frame_start)

        frame_end = max(all_frames)
        if frame_end > self.__frame_end:
            frame_end = self.__frame_end
            all_frames.add(frame_end)

        all_frames = sorted(all_frames)
        all_keys = [i.sampleFrames(all_frames) for i in curves]
        #return zip(all_frames, *all_keys)
        for data in zip(all_frames, *all_keys):
            frame_number = data[0]
            if frame_number < frame_start:
                continue
            if frame_number > frame_end:
                break
            yield data

    @staticmethod
    def __minRotationDiff(prev_q, curr_q):
        pq, q = prev_q, curr_q
        nq = q.copy()
        nq.negate()
        t1 = (pq.w-q.w)**2+(pq.x-q.x)**2+(pq.y-q.y)**2+(pq.z-q.z)**2
        t2 = (pq.w-nq.w)**2+(pq.x-nq.x)**2+(pq.y-nq.y)**2+(pq.z-nq.z)**2
        #t1 = pq.rotation_difference(q).angle
        #t2 = pq.rotation_difference(nq).angle
        if t2 < t1:
            return nq
        return q

    @staticmethod
    def __getVMDBoneInterpolation(x_axis, y_axis, z_axis, rotation):
        x_x1, x_y1 = x_axis[0]
        x_x2, x_y2 = x_axis[1]
        y_x1, y_y1 = y_axis[0]
        y_x2, y_y2 = y_axis[1]
        z_x1, z_y1 = z_axis[0]
        z_x2, z_y2 = z_axis[1]
        r_x1, r_y1 = rotation[0]
        r_x2, r_y2 = rotation[1]
        #return [ # minimum acceptable data
        #    x_x1, 0, 0, 0, x_y1, 0, 0, 0, x_x2, 0, 0, 0, x_y2, 0, 0, 0,
        #    y_x1, 0, 0, 0, y_y1, 0, 0, 0, y_x2, 0, 0, 0, y_y2, 0, 0, 0,
        #    z_x1, 0, 0, 0, z_y1, 0, 0, 0, z_x2, 0, 0, 0, z_y2, 0, 0, 0,
        #    r_x1, 0, 0, 0, r_y1, 0, 0, 0, r_x2, 0, 0, 0, r_y2, 0, 0, 0,
        #    ]
        return [ # full data, indices in [2, 3, 31, 46, 47, 61, 62, 63] are unclear
            x_x1, y_x1, z_x1, r_x1, x_y1, y_y1, z_y1, r_y1, x_x2, y_x2, z_x2, r_x2, x_y2, y_y2, z_y2, r_y2,
            y_x1, z_x1, r_x1, x_y1, y_y1, z_y1, r_y1, x_x2, y_x2, z_x2, r_x2, x_y2, y_y2, z_y2, r_y2,    0,
            z_x1, r_x1, x_y1, y_y1, z_y1, r_y1, x_x2, y_x2, z_x2, r_x2, x_y2, y_y2, z_y2, r_y2,    0,    0,
            r_x1, x_y1, y_y1, z_y1, r_y1, x_x2, y_x2, z_x2, r_x2, x_y2, y_y2, z_y2, r_y2,    0,    0,    0,
            ]

    @staticmethod
    def __pickRotationInterpolation(rotation_interps):
        for ir in rotation_interps:
            if ir != ((20, 20), (107, 107)):
                return ir
        return ((20, 20), (107, 107))


    def __exportBoneAnimation(self, armObj):
        if armObj is None:
            return None
        animation_data = armObj.animation_data
        if animation_data is None or animation_data.action is None:
            logging.warning('[WARNING] armature "%s" has no animation data', armObj.name)
            return None

        vmd_bone_anim = vmd.BoneAnimation()

        anim_bones = {}
        rePath = re.compile(r'^pose\.bones\["(.+)"\]\.([a-z_]+)$')
        for fcurve in animation_data.action.fcurves:
            m = rePath.match(fcurve.data_path)
            if m is None:
                continue
            bone = armObj.pose.bones.get(m.group(1), None)
            if bone is None:
                logging.warning(' * Bone not found: %s', m.group(1))
                continue
            if bone.is_mmd_shadow_bone:
                continue
            prop_name = m.group(2)
            if prop_name not in {'location', 'rotation_quaternion'}:
                continue

            if bone not in anim_bones:
                data = list(bone.location) + list(bone.rotation_quaternion)
                anim_bones[bone] = [_FCurve(i) for i in data] # x, y, z, rw, rx, ry, rz
            bone_curves = anim_bones[bone]
            if prop_name == 'location': # x, y, z
                bone_curves[fcurve.array_index].setFCurve(fcurve)
            elif prop_name == 'rotation_quaternion': # rw, rx, ry, rz
                bone_curves[3+fcurve.array_index].setFCurve(fcurve)

        for bone, bone_curves in anim_bones.items():
            key_name = bone.mmd_bone.name_j or bone.name
            assert(key_name not in vmd_bone_anim) # VMD bone name collision
            frame_keys = vmd_bone_anim[key_name]

            converter = self.__bone_converter_cls(bone, self.__scale, invert=True)
            prev_rot = None
            for frame_number, x, y, z, rw, rx, ry, rz in self.__allFrameKeys(bone_curves):
                key = vmd.BoneFrameKey()
                key.frame_number = frame_number - self.__frame_start
                key.location = converter.convert_location([x[0], y[0], z[0]])
                curr_rot = converter.convert_rotation([rx[0], ry[0], rz[0], rw[0]])
                if prev_rot is not None:
                    curr_rot = self.__minRotationDiff(prev_rot, curr_rot)
                prev_rot = curr_rot
                key.rotation = curr_rot[1:] + curr_rot[0:1] # (w, x, y, z) to (x, y, z, w)
                #FIXME we can only choose one interpolation from (rw, rx, ry, rz) for bone's rotation
                ir = self.__pickRotationInterpolation([rw[1], rx[1], ry[1], rz[1]])
                key.interp = self.__getVMDBoneInterpolation(x[1], z[1], y[1], ir) # x, z, y, q
                frame_keys.append(key)
            logging.info('(bone) frames:%5d  name: %s', len(frame_keys), key_name)
        return vmd_bone_anim


    def __exportMorphAnimation(self, meshObj):
        if meshObj is None:
            return None
        if meshObj.data.shape_keys is None:
            logging.warning('[WARNING] mesh "%s" has no shape keys', meshObj.name)
            return None
        animation_data = meshObj.data.shape_keys.animation_data
        if animation_data is None or animation_data.action is None:
            logging.warning('[WARNING] mesh "%s" has no animation data', meshObj.name)
            return None

        vmd_morph_anim = vmd.ShapeKeyAnimation()

        rePath = re.compile(r'^key_blocks\["(.+)"\]\.value$')
        for fcurve in animation_data.action.fcurves:
            m = rePath.match(fcurve.data_path)
            if m is None:
                continue

            key_name = m.group(1)
            kb = meshObj.data.shape_keys.key_blocks.get(key_name, None)
            if kb is None:
                logging.warning(' * Shape key not found: %s', key_name)
                continue

            assert(key_name not in vmd_morph_anim)
            anim = vmd_morph_anim[key_name]

            curve = _FCurve(kb.value)
            curve.setFCurve(fcurve)

            for frame_number, weight in self.__allFrameKeys([curve]):
                key = vmd.ShapeKeyFrameKey()
                key.frame_number = frame_number - self.__frame_start
                key.weight = weight[0]
                anim.append(key)
            logging.info('(mesh) frames:%5d  name: %s', len(anim), key_name)
        return vmd_morph_anim


    def __exportCameraAnimation(self, cameraObj):
        if cameraObj is None:
            return None
        if not MMDCamera.isMMDCamera(cameraObj):
            logging.warning('[WARNING] camera "%s" is not MMDCamera', cameraObj.name)
            return None

        cam_rig = MMDCamera(cameraObj)
        mmd_cam = cam_rig.object()
        camera = cam_rig.camera()

        vmd_cam_anim = vmd.CameraAnimation()

        data = list(mmd_cam.location) + list(mmd_cam.rotation_euler)
        data.append(mmd_cam.mmd_camera.angle)
        data.append(mmd_cam.mmd_camera.is_perspective)
        data.append(camera.location.y)
        cam_curves = [_FCurve(i) for i in data] # x, y, z, rx, ry, rz, fov, persp, distance

        animation_data = mmd_cam.animation_data
        if animation_data and animation_data.action:
            for fcurve in animation_data.action.fcurves:
                if fcurve.data_path == 'location': # x, y, z
                    cam_curves[fcurve.array_index].setFCurve(fcurve)
                elif fcurve.data_path == 'rotation_euler': # rx, ry, rz
                    cam_curves[3+fcurve.array_index].setFCurve(fcurve)
                elif fcurve.data_path == 'mmd_camera.angle': # fov
                    cam_curves[6].setFCurve(fcurve)
                elif fcurve.data_path == 'mmd_camera.is_perspective': # persp
                    cam_curves[7].setFCurve(fcurve)

        animation_data = camera.animation_data
        if animation_data and animation_data.action:
            for fcurve in animation_data.action.fcurves:
                if fcurve.data_path == 'location' and fcurve.array_index == 1: # distance
                    cam_curves[8].setFCurve(fcurve)

        for frame_number, x, y, z, rx, ry, rz, fov, persp, distance in self.__allFrameKeys(cam_curves):
            key = vmd.CameraKeyFrameKey()
            key.frame_number = frame_number - self.__frame_start
            key.location = [x[0]*self.__scale, z[0]*self.__scale, y[0]*self.__scale]
            key.rotation = [rx[0], rz[0], ry[0]] # euler
            key.angle = int(0.5 + math.degrees(fov[0]))
            key.distance = distance[0] * self.__scale
            key.persp = True if persp[0] else False

            #FIXME we can only choose one interpolation from (rx, ry, rz) for camera's rotation
            ir = self.__pickRotationInterpolation([rx[1], ry[1], rz[1]])
            ix, iy, iz, iD, iF = x[1], z[1], y[1], distance[1], fov[1]
            key.interp = [
                ix[0][0], ix[1][0], ix[0][1], ix[1][1],
                iy[0][0], iy[1][0], iy[0][1], iy[1][1],
                iz[0][0], iz[1][0], iz[0][1], iz[1][1],
                ir[0][0], ir[1][0], ir[0][1], ir[1][1],
                iD[0][0], iD[1][0], iD[0][1], iD[1][1],
                iF[0][0], iF[1][0], iF[0][1], iF[1][1],
                ]

            vmd_cam_anim.append(key)
        logging.info('(camera) frames:%5d  name: %s', len(vmd_cam_anim), mmd_cam.name)
        return vmd_cam_anim


    def __exportLampAnimation(self, lampObj):
        if lampObj is None:
            return None
        if not MMDLamp.isMMDLamp(lampObj):
            logging.warning('[WARNING] lamp "%s" is not MMDLamp', lampObj.name)
            return None

        lamp_rig = MMDLamp(lampObj)
        mmd_lamp = lamp_rig.object()
        lamp = lamp_rig.lamp()

        vmd_lamp_anim = vmd.LampAnimation()

        data = list(lamp.data.color) + list(lamp.location)
        lamp_curves = [_FCurve(i) for i in data] # r, g, b, x, y, z

        animation_data = lamp.data.animation_data
        if animation_data and animation_data.action:
            for fcurve in animation_data.action.fcurves:
                if fcurve.data_path == 'color': # r, g, b
                    lamp_curves[fcurve.array_index].setFCurve(fcurve)

        animation_data = lamp.animation_data
        if animation_data and animation_data.action:
            for fcurve in animation_data.action.fcurves:
                if fcurve.data_path == 'location': # x, y, z
                    lamp_curves[3+fcurve.array_index].setFCurve(fcurve)

        for frame_number, r, g, b, x, y, z in self.__allFrameKeys(lamp_curves):
            key = vmd.LampKeyFrameKey()
            key.frame_number = frame_number - self.__frame_start
            key.color = [r[0], g[0], b[0]]
            key.direction = [-x[0], -z[0], -y[0]]
            vmd_lamp_anim.append(key)
        logging.info('(lamp) frames:%5d  name: %s', len(vmd_lamp_anim), mmd_lamp.name)
        return vmd_lamp_anim


    def export(self, **args):
        armature = args.get('armature', None)
        mesh = args.get('mesh', None)
        camera = args.get('camera', None)
        lamp = args.get('lamp', None)
        filepath = args.get('filepath', '')

        self.__scale = args.get('scale', 1.0)

        if args.get('use_frame_range', False):
            self.__frame_start = bpy.context.scene.frame_start
            self.__frame_end = bpy.context.scene.frame_end

        if args.get('use_pose_mode', False):
            self.__bone_converter_cls = vmd.importer.BoneConverterPoseMode

        if armature or mesh:
            vmdFile = vmd.File()
            vmdFile.header = vmd.Header()
            vmdFile.header.model_name = args.get('model_name', '')
            vmdFile.boneAnimation = self.__exportBoneAnimation(armature)
            vmdFile.shapeKeyAnimation = self.__exportMorphAnimation(mesh)
            vmdFile.save(filepath=filepath)

        elif camera or lamp:
            vmdFile = vmd.File()
            vmdFile.header = vmd.Header()
            vmdFile.header.model_name = u'カメラ・照明'
            vmdFile.cameraAnimation = self.__exportCameraAnimation(camera)
            vmdFile.lampAnimation = self.__exportLampAnimation(lamp)
            vmdFile.save(filepath=filepath)
