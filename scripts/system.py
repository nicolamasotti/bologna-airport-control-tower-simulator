import os
import platform

from bge import render


def get_platform():
    return platform.system()


def init():
    system = get_platform()
    if system == 'Windows':
        os.system("cls")

    # activates mipmapping # setting this in the the User Preferences won't work for the Game Engine
    render.setMipmapping(2)  # can be 0, 1 or 2
    # activates anisotropic filtering # setting this in the the User Preferences won't work for the Game Engine
    render.setAnisotropicFiltering(4)  # can be up to 16
