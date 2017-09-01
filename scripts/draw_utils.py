# A collection of python utils

import mathutils
import my_types
from bge import logic


def draw_line(extents, time=0, color=(1, 1, 1, 1), offset=(0, 0, 0)):
    start = extents[0]
    end = extents[1]

    line = logic.getCurrentScene().addObject("Line", None, time)  # get the line from a different layer
    line.worldPosition = start + mathutils.Vector(offset)  # position the line origin where the segment should start
    target_vector = end - start  # get the vector from the star point of the segment to the end point
    target_rotation = target_vector.to_track_quat("Y", "Z")
    line.worldOrientation = target_rotation  # rotate the line according to the target rotation
    line.localScale.y = target_vector.length  # scale the line according to the segment length
    line.color = mathutils.Vector(color)


def display_nav_mesh(obj):
    if isinstance(obj, my_types.NavMesh):
        nav_dict = obj.nav_dict
        for node_key in nav_dict:
            node = nav_dict[node_key]
            node.reset()

            for neighbor_key in node.neighbors:
                neighbor = nav_dict[neighbor_key]

                start = node.location
                end = neighbor.location

                draw_line([start, end], time=0, color=(0.1, 0.1, 1, 1))
    else:
        raise Exception('Error: this objects is not a NavMesh')


def draw_taxi_route(taxi_route, time=0, color=(1, 1, 1, 1), offset=(0, 0, 0)):
    for i in range(len(taxi_route) - 1):
        draw_line(taxi_route[i:i + 2], time, color, offset)
