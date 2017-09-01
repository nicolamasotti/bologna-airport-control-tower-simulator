import manager
from bge import logic, render, events

W = render.getWindowWidth()
H = render.getWindowHeight()
cont = logic.getCurrentController()
mouse_sensor = cont.sensors[1]


def set_centred():  # sets the mouse to screen centre
    render.setMousePosition(W//2, H//2)


def get_pixel_position():  # gets the mouse position in pixels
    return round(logic.mouse.position[0] * W), round(logic.mouse.position[1] * H)
    # logic.mouse.position is the normalised screen position from 0 to 1


def get_pixel_movement():  # gets mouse movement within respect to screen center, in pixels
    movement = [0.5 - logic.mouse.position[0], 0.5 - logic.mouse.position[1]]
    x_pixel_movement = int(W * movement[0])
    y_pixel_movement = int(H * movement[1])
    return x_pixel_movement, y_pixel_movement


def left_click():  # returns True if the left mouse button has just been clicked
    if mouse_sensor.getButtonStatus(events.LEFTMOUSE) == logic.KX_INPUT_JUST_ACTIVATED:
        if manager.debug_mode:
            print('left click')
        return True
    else:
        return False


def right_click():  # returns True if the right mouse button has just been clicked
    if mouse_sensor.getButtonStatus(events.RIGHTMOUSE) == logic.KX_INPUT_JUST_ACTIVATED:
        if manager.debug_mode:
            print('right click')
        return True
    else:
        return False
