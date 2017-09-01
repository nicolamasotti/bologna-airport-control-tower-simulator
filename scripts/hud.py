import re
import os
from bge import logic, types

cont = logic.getCurrentController()
scene = logic.getCurrentScene()


def set_text_resolution():
    for obj in scene.objects:
        if isinstance(obj, types.KX_FontObject):
            obj.resolution = 8


def get_metar_data():
    module_path = os.path.dirname(__file__)
    metar_path = os.path.join(module_path, "../resources/METAR/METAR_LIPE.txt")
    # print(metar_path)

    with open(metar_path) as metar:
        for line in metar:
            fields = line.split()

    for field in fields:

        if re.match("FEW|SCT|BKN|OCV", field):
            ceiling_type = scene.objects['ceiling_type']
            ceiling_type.text = field[:3]
            ceiling_value = scene.objects['ceiling_value']
            ceiling_value.text = field[5] + '00'

        elif re.search("KT", field):

            wind_direction_value = scene.objects['wind_direction_value']
            wind_direction_value.text = field[:3]
            wind_speed_value = scene.objects['wind_speed_value']
            wind_speed_value.text = field[3:5]

        elif re.search("R", field) and re.search("/", field):
            rvr_value = scene.objects['rvr_value']
            runway, rvr_min, rvr_max, end_of_field = re.split('/|V|N', field)
            print(runway, rvr_min, rvr_max, end_of_field)

            if int(rvr_min) < 2000:  # or (int (visual_range_max) < 2000)
                rvr_value.text = rvr_min + "/\n/" + rvr_max
            else:
                rvr_value.text = ""

        elif re.search("Q", field):
            qnh_value = scene.objects['qnh_value']
            qnh_value.text = field[1:]
