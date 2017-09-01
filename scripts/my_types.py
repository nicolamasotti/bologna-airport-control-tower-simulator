#######################################################################################################################
# This script defines custom classes for the airport scenario

import math

import bge_utils
import draw_utils
import manager
import mouse_utils
import py_utils
from bge import logic, types, events

########################################################################################################################
keyboard = logic.keyboard
origin = logic.getCurrentScene().objects['Origin']


class Scene(types.KX_Scene):
    def __init__(self, scene_obj):
        self.taxi_objects = []
        self.selected_object = None

class RouteFinder:
    @staticmethod
    def search_taxi_route(obj):
        taxi_route = []
        for i in range(len(obj.waypoints) - 1):
            start_waypoint = obj.waypoints[i]
            end_waypoint = obj.waypoints[i + 1]
            start_node = bge_utils.get_nearest_node(start_waypoint, manager.nav_mesh.nav_dict)
            end_node = bge_utils.get_nearest_node(end_waypoint, manager.nav_mesh.nav_dict)
            # print(manager.nav_mesh.nav_dict[end_node].location)
            taxi_route.extend(bge_utils.a_star(manager.nav_mesh.nav_dict, start_node, end_node, obj.waypoints[-1]))
            for key in manager.nav_mesh.nav_dict:
                manager.nav_mesh.nav_dict[key].reset()
        # taxi_route.append(obj.waypoints[-1])
        if taxi_route:
            taxi_route.pop(0)
        # if manager.debug_mode:
        route_to_draw = [obj.worldPosition] + taxi_route
        draw_utils.draw_taxi_route(route_to_draw, time=1000, color=(0, 1, 0, 1), offset=(0, 0, 1))

        return taxi_route


class NavMesh(types.KX_GameObject):
    def __init__(self, game_obj):
        self.nav_dict = bge_utils.get_nav_mesh()
        if manager.debug_mode:
            draw_utils.display_nav_mesh(self)


class Interface:  # handles the interaction between the pseudo-pilot and the scene

    clicked_points = []

    @staticmethod
    def get_user_input(scene):

        hit_object = mouse_utils.mouse_sensor.hitObject  # get the last object the mouse was over
        # print(hit_object)

        if hit_object:  # if the hit object is not None

            # Handle left click
            if mouse_utils.left_click():  # in the user left clicks

                if "aircraft" in hit_object and hit_object is not scene.selected_object:
                    if scene.selected_object:
                        py_utils.clear_list(scene.selected_object.waypoints)  # clear its waypoints
                        py_utils.clear_list(scene.selected_object.taxi_route)
                    scene.selected_object = hit_object  # set the object to be the active object in the scene

                else:  # else, if it's not an aircraft
                    if scene.selected_object:
                        hit_position = mouse_utils.mouse_sensor.hitPosition  # get the hit position from the mouse
                        bge_utils.move_target_to(hit_position)  # move the target flag to the hit position
                        Interface.clicked_points.append(hit_position)

            # Handle right click
            elif mouse_utils.right_click():  # if the user right clicks

                if scene.selected_object:
                    py_utils.clear_list(scene.selected_object.waypoints)  # clear its waypoints
                    # py_utils.clear_list(scene.selected_object.taxi_route)
                    scene.selected_object = None  # set the selected object to none

                if 'aircraft' in hit_object:  # if it is an aircraft
                    py_utils.clear_list(hit_object.waypoints)  # clear its waypoints
                    py_utils.clear_list(hit_object.taxi_route)  # clear the path to the 1st waypoint
                    if hit_object in scene.taxi_objects:
                        scene.taxi_objects.remove(hit_object)  # remove the object from the taxi objects list

        # Handle the ENTERKEY press event
        if logic.keyboard.events[events.ENTERKEY] == logic.KX_INPUT_JUST_ACTIVATED:
            # print("ENTERKEY")
            if scene.selected_object:
                scene.selected_object.waypoints.extend(Interface.clicked_points)
                Interface.clicked_points = []

                scene.selected_object = None
