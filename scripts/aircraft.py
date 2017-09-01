import bge_utils
import manager
import mathutils
import my_types
import py_utils
import math
from bge import logic, events, types

keyboard = logic.keyboard


class Aircraft(types.KX_GameObject):
    def __init__(self, game_obj):
        self.ground_position = mathutils.Vector((self.worldPosition[0], self.worldPosition[1], 0))
        self.waypoints = []
        self.taxi_route = []
        self.states = []
        self.always_sensor = self.sensors['Always']
        self.take_off_actuator = self.actuators['Take_off']
        self.landing_actuator = self.actuators['Land']

    def idle(self):
        pass

    def taxi(self):
        if self.taxi_route:
            self.ground_position = mathutils.Vector((self.worldPosition[0], self.worldPosition[1], 0))
            delta = self.taxi_route[0] - self.ground_position
            self.setLinearVelocity([self['linear_velocity'], 0, 0], True)
            self.alignAxisToVect(delta, 0, self['angular_velocity'])
            if self.has_reached(self.taxi_route[0]):
                self.taxi_route.pop(0)
        else:
            self.states.remove(self.taxi)

    def landing_start(self):
        self.always_sensor.invert = False
        logic.getCurrentController().activate(self.landing_actuator)
        self.states.remove(self.landing_start)
        self.states.append(self.landing)

    def landing(self):
        pass

    def take_off_start(self):
        self.always_sensor.invert = False
        logic.getCurrentController().activate(self.take_off_actuator)
        self.states.remove(self.take_off_start)
        self.states.append(self.taking_off)

    def taking_off(self):
        pass

    def has_reached(self, point):
        if math.fabs((self.ground_position - point).magnitude) < 3:
            return True
        else:
            return False


def main(cont):
    own = cont.owner
    scene = logic.getCurrentScene()
    first_hit_on_runway = scene.objects['Ray_start_empty'].rayCastTo(scene.objects['Ray_end_empty'])

    if 'aircraft_init' not in own:
        init(own)

    else:

        if own.waypoints:
            nearest_node_key = bge_utils.get_nearest_node(own.worldPosition, manager.nav_mesh.nav_dict)
            nearest_node = manager.nav_mesh.nav_dict[nearest_node_key]
            own.waypoints = [nearest_node.location] + own.waypoints
            own.taxi_route = my_types.RouteFinder.search_taxi_route(own)
            py_utils.clear_list(own.waypoints)

        if not own.states:
            own.states.append(own.idle)

        if own.idle in own.states:
            if own.taxi_route:
                own.states.remove(own.idle)
                own.states.append(own.taxi)

            elif first_hit_on_runway is own and keyboard.events[events.TKEY] == logic.KX_INPUT_JUST_ACTIVATED:
                own.states.remove(own.idle)
                own.states.append(own.take_off_start)

        #print(own.states)
        for state in own.states:
            state()


def init(own):
    if own.getDistanceTo([0, 0, 0]) > 2000:
        own.states.append(own.landing_start)

    else:
        own.states.append(own.idle)

    own['aircraft_init'] = True
