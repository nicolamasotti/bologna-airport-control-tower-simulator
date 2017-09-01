# This script handles the viewport for a 3 screen V/AR system
# the position of the screens corners are retrieved from the Blender Scene

from enum import Enum

import bge_utils
from bge import logic, types, render, events
from mathutils import Matrix, Vector

# Global variables

gD = logic.globalDict
skt = None
tracker = None
head = None
left_eye = None
right_eye = None
view_mode = None
keyboard = logic.keyboard
mouse = logic.mouse

# Global constants

W = render.getWindowWidth()
H = render.getWindowHeight()
LEFT_EYE = render.LEFT_EYE
RIGHT_EYE = render.RIGHT_EYE
EYE_SEPARATION = 0.06
DELTA_MOVE_TOP_VIEW = 10


# Classes

class ViewMode(Enum):
    TOWER_VIEW = 0
    TOP_VIEW = 1


# a class that handles monoscopic pre-draw
class Mono:
    # settings for top view camera
    top_view_camera = logic.getCurrentScene().objects["Top_view_camera"]
    n = top_view_camera.near
    f = top_view_camera.far
    TOP_VIEW_CAMERA_PROJECTION_MATRIX = Matrix.Identity(4)
    TOP_VIEW_CAMERA_PROJECTION_MATRIX.zero()
    TOP_VIEW_CAMERA_PROJECTION_MATRIX[0][0] = n / 3
    TOP_VIEW_CAMERA_PROJECTION_MATRIX[1][1] = n / 1
    TOP_VIEW_CAMERA_PROJECTION_MATRIX[2][2] = -((f + n) / (f - n))
    TOP_VIEW_CAMERA_PROJECTION_MATRIX[2][3] = -((2 * f * n) / (f - n))
    TOP_VIEW_CAMERA_PROJECTION_MATRIX[3][2] = -1

    @staticmethod
    def pre_draw_setup_for_top_view_camera():
        Mono.top_view_camera.projection_matrix = Mono.TOP_VIEW_CAMERA_PROJECTION_MATRIX


# a class that handles stereo pre-draw
class Stereo:
    @staticmethod
    def get_current_eye_object():

        try:
            if render.getStereoEye() == 1:
                return left_eye
            elif render.getStereoEye() == 2:
                return right_eye
        except:
            raise Exception('Stereo is not active or supported')

    @staticmethod
    def pre_draw_setup_for_CAVE():

        for obj in logic.getCurrentScene().objects:
            if type(obj) == Camera:
                obj.worldPosition = Stereo.get_current_eye_object().worldPosition

        for eye in left_eye, right_eye:
            if eye.side == render.getStereoEye():
                for n in range(1, 4):
                    if 'projection' + str(n) in eye:
                        eye['projection' + str(n)].projection_cycle()


# A class that represents the tracking system
class Tracker(types.KX_GameObject):
    def __init__(self, empty):
        self.t = self.worldPosition  # This is the translation vector from tracker-space to world-space
        self.R = self.orientation.transposed()


# A derived class for Blender Camera objects
class Camera(types.KX_Camera):
    def __init__(self, camera):
        # this is for the triple screen config
        self.number = self['number']
        self.left = int(round(W * (self.number - 1) * 1 / 3))
        self.bottom = 0
        self.right = int(round(W * self.number * 1 / 3))
        self.top = H
        self.setViewport(self.left, self.bottom, self.right, self.top)
        self.useViewport = True


# a derived class representing the V/AR screens
class Screen(types.KX_GameObject):
    def __init__(self, plane):
        self.number = self['number']
        for child in self.children:
            if 'screen' not in child:
                setattr(self, child.name[0:2], child.worldPosition)
                # stands for self.p = p.worldPosition, for p in [pa,pb,pc]


# a derived class representing the viewer's head.
class Head(types.KX_GameObject):
    def __init__(self, empty):
        pass

    def set_head_position(self):
        if gD:
            self.worldPosition = (gD['head_position_in_tracker_space'] * tracker.R) + tracker.t
            # print("Head worldPosition is: {}".format(self.worldPosition))
        else:
            # print("GlobalDict is empty, not updating head position")
            pass


# a derived class representing the viewer's eyes
class Eye(types.KX_GameObject):
    def __init__(self, empty):
        if 'left' in self:
            self.worldPosition -= Vector((EYE_SEPARATION / 2, 0, 0))
            self.side = 1

        elif 'right' in self:
            self.worldPosition += Vector((EYE_SEPARATION / 2, 0, 0))
            self.side = 2


# Each instance of this class handles the projections for a single eye-screen pair
class Projection:
    def __init__(self, camera, screen):
        self.camera = camera
        self.screen = screen

        # set the near and far clipping planes distances for the current projection
        # keep the ones defined in Blender UI
        self.n = camera.near
        self.f = camera.far

        self.va = None
        self.vb = None
        self.vc = None

        self.sr = None
        self.su = None
        self.sn = None

        self.l = None
        self.r = None
        self.b = None
        self.t = None

        self.d = None

        self.M = None
        self.P = None

    def projection_cycle(self):
        self.update_frustum_edges()
        self.compute_screen_orthonormal_basis()
        self.update_distance_to_screen()
        self.update_screen_extents()
        self.update_projection_matrix()

    def update_frustum_edges(self):
        # convert screen corners' world coordinates into eye-space coordinates
        # these are the frustum edges in eye space
        self.va = self.camera.world_to_camera * self.screen.pa
        self.vb = self.camera.world_to_camera * self.screen.pb
        self.vc = self.camera.world_to_camera * self.screen.pc

    def compute_screen_orthonormal_basis(self):
        # compute an otho-normal basis that defines the screen's local coordinate system orientation
        self.sr = (self.vb - self.va)
        self.sr.normalize()
        self.su = (self.vc - self.va)
        self.su.normalize()
        self.sn = self.sr.cross(self.su)
        self.sn.normalize()

        # compute the transformation matrix that maps the screen space coordinate system
        # onto the camera space coordinate system transforming the otho-normal basis (sr,su,sn)
        # into camera space basis (x,y,z)

        self.M = Matrix.Identity(4)
        self.M.zero()

        self.M[0][0] = self.sr[0]
        self.M[0][1] = self.sr[1]
        self.M[0][2] = self.sr[2]
        self.M[1][0] = self.su[0]
        self.M[1][1] = self.su[1]
        self.M[1][2] = self.su[2]
        self.M[2][0] = self.sn[0]
        self.M[2][1] = self.sn[1]
        self.M[2][2] = self.sn[2]
        self.M[3][3] = 1

    def update_distance_to_screen(self):
        # compute the distance from eye to screen plane
        self.d = -self.sn.dot(self.va)

    def update_screen_extents(self):
        # find the screen extents of the perpendicular off-axis perspective projection and scale them
        # to the near clipping plane
        self.l = self.sr.dot(self.va) * self.n / self.d
        self.r = self.sr.dot(self.vb) * self.n / self.d
        self.b = self.su.dot(self.va) * self.n / self.d
        self.t = self.su.dot(self.vc) * self.n / self.d

    def update_projection_matrix(self):
        # build the standard 3D perspective projection matrix for the current frustum
        self.P = Matrix.Identity(4)
        self.P.zero()

        self.P[0][0] = 2 * self.n / (self.r - self.l)
        self.P[0][2] = (self.r + self.l) / (self.r - self.l)
        self.P[1][1] = 2 * self.n / (self.t - self.b)
        self.P[1][2] = (self.t + self.b) / (self.t - self.b)
        self.P[2][2] = -(self.f + self.n) / (self.f - self.n)
        self.P[2][3] = -2 * self.f * self.n / (self.f - self.n)
        self.P[3][2] = -1

        # set the final projection matrix as the composition of everything
        self.camera.projection_matrix = self.P * self.M


# Module execution entry point


def main(cont):
    global view_mode
    own = cont.owner
    scene = logic.getCurrentScene()

    if 'viewport_init' not in own:
        init(cont, own)


    else:

        global view_mode

        scene = logic.getCurrentScene()

        if keyboard.events[events.OKEY] == logic.KX_INPUT_JUST_ACTIVATED:
            scene.active_camera = scene.objects['Top_view_camera']
        elif keyboard.events[events.IKEY] == logic.KX_INPUT_JUST_ACTIVATED:
            scene.active_camera = scene.objects['Central_camera']

        if scene.active_camera == scene.objects['Top_view_camera']:
            current_view_mode = ViewMode.TOP_VIEW
            #print("view mode is ", view_mode)
            #print("current view mode is", current_view_mode)

            if current_view_mode != view_mode:
                #print("changing from TOWER to TOP")
                for obj in scene.objects:
                    if type(obj) == Camera:
                        obj.useViewport = False
                # there is no need to explicitly set useViewport = True for the Top_view_camera
                # this already happens via logic bricks
                # actually if I do that it doesn't work anymore for some unknown reason
                scene.pre_draw_setup = [Mono.pre_draw_setup_for_top_view_camera]
                view_mode = ViewMode.TOP_VIEW
            else:
                pass

        else:
            current_view_mode = ViewMode.TOWER_VIEW
            #print("view mode is ", view_mode)
            #print("current view mode is", current_view_mode)

            if current_view_mode != view_mode:
                #print("changing from TOP to TOWER")
                for obj in scene.objects:
                    if type(obj) == Camera:
                        obj.useViewport = True
                # I could have explicitly set useViewport = False for the Top_view_camera
                # however this seems to already happen because of the logic bricks setup
                scene.pre_draw_setup = [Stereo.pre_draw_setup_for_CAVE]
                view_mode = ViewMode.TOWER_VIEW
            else:
                pass

        camera = scene.active_camera

        if view_mode == ViewMode.TOP_VIEW:

            if keyboard.events[events.AKEY] == logic.KX_INPUT_ACTIVE:
                bge_utils.move_x(camera, DELTA_MOVE_TOP_VIEW, -1, False)
            if keyboard.events[events.DKEY] == logic.KX_INPUT_ACTIVE:
                bge_utils.move_x(camera, DELTA_MOVE_TOP_VIEW, 1, False)
            if keyboard.events[events.WKEY] == logic.KX_INPUT_ACTIVE:
                bge_utils.move_y(camera, DELTA_MOVE_TOP_VIEW, 1, False)
            if keyboard.events[events.SKEY] == logic.KX_INPUT_ACTIVE:
                bge_utils.move_y(camera, DELTA_MOVE_TOP_VIEW, -1, False)

            if mouse.events[events.WHEELUPMOUSE] == logic.KX_INPUT_ACTIVE:
                bge_utils.move_z(camera, DELTA_MOVE_TOP_VIEW, 1, False)
            if mouse.events[events.WHEELDOWNMOUSE] == logic.KX_INPUT_ACTIVE:
                bge_utils.move_z(camera, DELTA_MOVE_TOP_VIEW, -1, False)

        if view_mode == ViewMode.TOWER_VIEW:

            try:
                head.set_head_position()
                # for eye in left_eye, right_eye:
                # print("{} worldPosition is: {}".format(eye, eye.worldPosition))
            except:
                print('Some issue setting head position')
                raise


# initialization function that runs once


def init(cont, own):
    global view_mode

    scene = logic.getCurrentScene()
    objects = scene.objects

    try:
        render.setEyeSeparation(0.0)

        try:
            for obj in objects:

                if 'tracker' in obj:
                    global tracker
                    tracker = Tracker(obj)

                elif 'head' in obj:
                    global head
                    head = Head(obj)

                elif 'eye' in obj:
                    if 'left' in obj:
                        global left_eye
                        left_eye = Eye(obj)

                    elif 'right' in obj:
                        global right_eye
                        right_eye = Eye(obj)

                elif 'screen' in obj:
                    Screen(obj)

            if '__default__cam__' not in scene.cameras:  # if in 'Active Camera' view
                for camera in scene.cameras:
                    if 'number' in camera:
                        Camera(camera)  # re-instancing KX_Camera objects
        except:
            print("Failed to re-instance some Blender object")
            raise

        for obj in objects:

            if type(obj) == Eye:

                eye = obj
                for n in range(1, 4):

                    screen = None
                    camera = None
                    for object in objects:

                        if type(object) == Screen:

                            if object['number'] == n:
                                screen = object

                        if type(object) == Camera:

                            if object['number'] == n:
                                camera = object

                    if screen is not None and camera is not None:
                        eye['projection' + str(n)] = Projection(camera, screen)
                        #print(eye['projection' + str(n)])
                        # may be set as an attribute as well
                        # setattr(eye, 'projection'+str(n), Projection(camera, screen))

        # logic.getCurrentScene().pre_draw_setup.append(Stereo.pre_draw_setup_for_CAVE)

        if scene.active_camera == scene.objects['Top_view_camera']:
            view_mode = ViewMode.TOP_VIEW
            scene.pre_draw_setup = [Mono.pre_draw_setup_for_top_view_camera]


        else:
            view_mode = ViewMode.TOWER_VIEW
            scene.pre_draw_setup = [Stereo.pre_draw_setup_for_CAVE]

        own['viewport_init'] = True

    except:
        print("Viewport initialization failed")
        raise
