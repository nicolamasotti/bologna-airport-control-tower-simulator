from bge import logic

# init parameters, change this is you want to activate/deactivate overlays at start

RUNWAY_OVERLAY_ON = True
BOUNDING_CIRCLE_OVERLAY_ON = True


def runway_is_occupied():
    objects = logic.getCurrentScene().objects
    hit_object = objects['Ray_start_empty'].rayCastTo(objects['Ray_end_empty'])
    if hit_object is not None:
        return True
    else:
        return False


def main(cont):
    scene = logic.getCurrentScene()
    own = cont.owner
    if 'overlay_init' not in own:
        init(own)
    else:
        if runway_is_occupied():
            if 'Runway_overlay_green' in scene.objects:
                scene.objects['Runway_overlay_green'].endObject()
            if 'Runway_overlay_red' not in scene.objects:
                scene.addObject('Runway_overlay_red')
        else:
            if 'Runway_overlay_red' in scene.objects:
                scene.objects['Runway_overlay_red'].endObject()
            if 'Runway_overlay_green' not in scene.objects:
                scene.addObject('Runway_overlay_green')


def init(own):
    scene = logic.getCurrentScene()

    if RUNWAY_OVERLAY_ON:
        #print(scene.objects)
        scene.objects['Runway_group'].endObject()
        scene.objects['Runway'].endObject()
        #print('runway killed 2 times!!')

        if runway_is_occupied():
            scene.addObject('Runway_overlay_red')
        else:
            scene.addObject('Runway_overlay_green')

        scene.addObject('Runway_overlay_ground_lines')

    own['overlay_init'] = True
