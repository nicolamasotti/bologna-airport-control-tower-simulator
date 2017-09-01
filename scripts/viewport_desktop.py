# This script handles the viewport for a typical desktop system

from enum import Enum

import bge_utils
from bge import logic, events

scene = logic.getCurrentScene()
keyboard = logic.keyboard
mouse = logic.mouse
view_mode = None
DELTA_MOVE_TOWER_VIEW = 0.2
DELTA_MOVE_TOP_VIEW = 10
DELTA_ROT = 0.05


class ViewMode(Enum):
    TOWER_VIEW = 0
    TOP_VIEW = 1


def get_user_input():
    global view_mode
    scene = logic.getCurrentScene()

    if keyboard.events[events.OKEY] == logic.KX_INPUT_JUST_ACTIVATED:
        view_mode = ViewMode.TOP_VIEW
        scene.active_camera = scene.objects['Top_view_camera']
    elif keyboard.events[events.IKEY] == logic.KX_INPUT_JUST_ACTIVATED:
        view_mode = ViewMode.TOWER_VIEW
        scene.active_camera = scene.objects['Central_camera']

    camera = scene.active_camera

    if view_mode == ViewMode.TOWER_VIEW:

        if keyboard.events[events.AKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.move_x(camera, DELTA_MOVE_TOWER_VIEW, -1, True)
        if keyboard.events[events.DKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.move_x(camera, DELTA_MOVE_TOWER_VIEW, 1, True)
        if keyboard.events[events.WKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.move_z(camera, DELTA_MOVE_TOWER_VIEW, -1, True)
        if keyboard.events[events.SKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.move_z(camera, DELTA_MOVE_TOWER_VIEW, 1, True)

        if keyboard.events[events.LEFTARROWKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.turn_z(camera, DELTA_ROT, 1, False)
        if keyboard.events[events.RIGHTARROWKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.turn_z(camera, DELTA_ROT, -1, False)
        if keyboard.events[events.UPARROWKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.turn_x(camera, DELTA_ROT, 1, True)
        if keyboard.events[events.DOWNARROWKEY] == logic.KX_INPUT_ACTIVE:
            bge_utils.turn_x(camera, DELTA_ROT, -1, True)

        if mouse.events[events.WHEELUPMOUSE] == logic.KX_INPUT_ACTIVE:
            bge_utils.move_z(camera, DELTA_MOVE_TOWER_VIEW, 1, False)
        if mouse.events[events.WHEELDOWNMOUSE] == logic.KX_INPUT_ACTIVE:
            bge_utils.move_z(camera, DELTA_MOVE_TOWER_VIEW, -1, False)

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


def set_initial_view_mode():
    global view_mode
    camera = logic.getCurrentScene().active_camera
    if camera is logic.getCurrentScene().objects['Central_camera']:
        view_mode = ViewMode.TOWER_VIEW
    elif camera is logic.getCurrentScene().objects['Top_view_camera']:
        view_mode = ViewMode.TOP_VIEW


# Module execution entry point
def main(cont):
    own = cont.owner
    if 'camera_init' not in own:
        set_initial_view_mode()
        own['camera_init'] = True
    else:
        get_user_input()
