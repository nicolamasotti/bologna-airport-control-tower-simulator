########################################################################################################################
# This script initialises the navigation mesh and manages mobile objects in the scene

import my_types
import aircraft
from bge import logic

########################################################################################################################

debug_mode = None  # this is set through a property of the script owner
nav_mesh = None


########################################################################################################################

# Module execution entry point


def main(cont):
    own = cont.owner

    if 'init' not in own:
        try:
            init(own)
            own['init'] = True

        except UserWarning:
            print("Error: Manager initialization failed")
    else:
        my_types.Interface.get_user_input(logic.getCurrentScene())

########################################################################################################################


def init(own):
    # try to set the debug flag
    try:
        global debug_mode
        debug_mode = own['debug']
    except KeyError:
        print('KeyError: script owner has no debug property')

    # re-instancing the current Scene
    my_types.Scene(logic.getCurrentScene())

    # re-instancing objects in the scene
    for obj in logic.getCurrentScene().objects:

        if 'aircraft' in obj:
            aircraft.Aircraft(obj)  # re-instancing all aircraft objects

        elif "navmesh" in obj:
            global nav_mesh
            nav_mesh = my_types.NavMesh(obj)
