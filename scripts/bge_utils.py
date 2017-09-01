import heapq
import threading

import mathutils
from bge import logic


class NavThread(threading.Thread):
    def __init__(self, manager):
        threading.Thread.__init__(self)
        self.manager = manager
        self.cont = self.manager.cont

    def run(self):
        navigation = get_nav_mesh()
        self.manager.nav_dict = navigation
        self.manager.navi_generated = True


class NavNode(object):
    def __init__(self, manager, location, poly_points):
        self.manager = manager
        self.location = location
        self.g = 0.0
        self.f = 9000.0
        self.neighbors = {}
        self.parent = None
        self.corners = poly_points
        self.blocked = False

    def reset(self):
        self.g = 0.0
        self.f = 9000.0
        self.parent = None


class NeighborNode(object):
    def __init__(self, location, distance):
        self.location = location
        self.distance = distance
        self.cost = 1.0


# check if a line from one object to another collides with an object
def two_dee_bounding_box(blender_object):
    points = []
    mesh = blender_object.meshes[0]
    v_length = mesh.getVertexArrayLength(0)

    for v in range(v_length):
        vertex = mesh.getVertex(0, v)
        point = vertex.getXYZ()
        points.append(point.to_2d())

    x_range = [point.x for point in points]
    y_range = [point.y for point in points]

    point_1 = mathutils.Vector([min(x_range), min(y_range)])
    point_2 = mathutils.Vector([min(x_range), max(y_range)])
    point_3 = mathutils.Vector([max(x_range), max(y_range)])
    point_4 = mathutils.Vector([max(x_range), min(y_range)])

    box = [point_1, point_2, point_3, point_4]
    return box


def get_key(xy):
    string_key = "{}${}".format(str(xy[0]), str(xy[1]))

    return string_key


def get_obs(string, lst):
    obs = [obj for obj in lst if string in obj]
    # print(obs)

    if obs:
        return obs

    return None


def move_target_to(position):
    target = logic.getCurrentScene().addObject("Waypoint", None, 500)
    target.worldPosition = position


def get_point(xyz_pos, transform):
    offset_matrix = mathutils.Matrix.Translation(xyz_pos)

    mat_out = (transform * offset_matrix).decompose()
    point = mat_out[0]

    return point


def get_point_details(own, point_location, assigned_dict, poly_points):
    key_code = (int(point_location[0] * 10.0), int(point_location[1] * 10.0))
    node_key = get_key(key_code)

    if node_key not in assigned_dict:
        new_node = NavNode(own, point_location, poly_points)

        assigned_dict[node_key] = new_node


def get_nav_mesh():
    cont = logic.getCurrentController()
    own = cont.owner
    scene = own.scene
    walkmeshes = get_obs("navmesh", scene.objects)

    nav_dict = {}

    for walk_mesh in walkmeshes:
        mesh = walk_mesh.meshes[0]

    poly_length = mesh.numPolygons

    for polyID in range(poly_length):
        poly_points = []
        poly = mesh.getPolygon(polyID)

        vert_length = poly.getNumVertex()

        for v in range(vert_length):
            index = poly.getVertexIndex(v)

            vertex = mesh.getVertex(0, index)
            v_loc = vertex.getXYZ()
            v_loc.z += 0.1

            point = get_point(v_loc, walk_mesh.worldTransform)

            poly_points.append(point)

        if poly_points:

            poly_center = mathutils.Vector()

            for point in poly_points:
                poly_center += point

            poly_center = poly_center / vert_length

            get_point_details(own, poly_center, nav_dict, poly_points)

    return find_neighbors(nav_dict)


def find_neighbors(nav_dict):
    for node_key in nav_dict:
        node = nav_dict[node_key]

        for other_key in nav_dict:
            other_node = nav_dict[other_key]

            match_count = 0

            node_corners = node.corners
            other_corners = other_node.corners

            for corner in node_corners:
                for other_corner in other_corners:
                    check_1 = corner.to_tuple(1)
                    check_2 = other_corner.to_tuple(1)

                    if check_1 == check_2:
                        match_count += 1

            if match_count > 1:
                neighbor_dict = {}

                distance_vector = other_node.location - node.location
                distance = distance_vector.length

                node.neighbors[other_key] = NeighborNode(other_node.location, distance)

    return nav_dict


def get_nearest_node(target, graph):
    keys = [[key, graph[key]] for key in graph]
    sorted_keys = sorted(keys, key=lambda self, other=target: (self[1].location - other).length)
    best_keys = [key[0] for key in sorted_keys][:3]
    if best_keys:
        return best_keys[0]
    else:
        return None


        ### A* algorithm function


def a_star(graph, current_key, end_key, goal):
    open_set = set()
    open_heap = []
    closed_set = set()

    path = []
    found = 0

    #####################################
    def path_gen(current_key, graph):

        current = graph[current_key]
        path = [current.location]

        while current.parent != None:
            current = graph[current.parent]

            path.append(current.location)

        return path

    ######################################

    open_set.add(current_key)
    open_heap.append((0, current_key))

    while found == 0 and open_set:

        current_key = heapq.heappop(open_heap)[1]

        if current_key == end_key:
            path = path_gen(current_key, graph)
            found = 1

        open_set.remove(current_key)
        closed_set.add(current_key)

        current_node = graph[current_key]

        for neighbor_key in current_node.neighbors:
            if neighbor_key in graph:

                neighbor = current_node.neighbors[neighbor_key]

                if not graph[neighbor_key].blocked:

                    neighbor_distance = neighbor.distance * neighbor.cost
                    g_score = current_node.g + neighbor_distance
                    relation = goal - neighbor.location

                    if neighbor_key in closed_set and g_score >= graph[neighbor_key].g:
                        continue

                    if neighbor_key not in open_set or g_score < graph[neighbor_key].g:
                        graph[neighbor_key].parent = current_key
                        graph[neighbor_key].g = g_score

                        h_score = relation.length
                        f_score = g_score + h_score
                        graph[neighbor_key].f = f_score

                        if neighbor_key not in open_set:
                            open_set.add(neighbor_key)
                            heapq.heappush(open_heap, (graph[neighbor_key].f, neighbor_key))

    if path:
        path.reverse()

    return path


def move_x(game_obj, delta, direction, local):
    game_obj.applyMovement(mathutils.Vector((delta * direction, 0, 0)), local)


def move_z(game_obj, delta, direction, local):
    game_obj.applyMovement(mathutils.Vector((0, 0, delta * direction)), local)


def move_y(game_obj, delta, direction, local):
    game_obj.applyMovement(mathutils.Vector((0, delta * direction, 0)), local)


def turn_x(game_obj, delta, direction, local):
    game_obj.applyRotation(mathutils.Vector((delta * direction, 0, 0)), local)


def turn_z(game_obj, delta, direction, local):
    game_obj.applyRotation(mathutils.Vector((0, 0, delta * direction)), local)
