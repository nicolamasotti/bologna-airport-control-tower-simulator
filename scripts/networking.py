# This script receives head coordinates data from the network

import socket
import bge
from bge import logic
from mathutils import Vector

# Global variables

gD = logic.globalDict  # shorten the syntax
skt = None


# Classes


# a class that defines a custom socket
class Socket(socket.socket):
    def __init__(self, *args):
        super().__init__(args[0], args[1])
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setblocking(False)  # set socket to non-blocking mode
        # SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state
        # without waiting for its natural timeout to expire
        self.bind(("127.0.0.1", 9999))
        print('Socket bind to IP 127.0.0.1 and port 9999')

    def receive(self):
        # print("Trying to receive data from network")
        try:
            data, addr = self.recvfrom(1024)
            message = data.decode('Utf8').splitlines()
            current_head_position_in_tracker_space = Vector((float(message[0].replace(',', '.')),
                                                             float(message[1].replace(',', '.')),
                                                             float(message[2].replace(',', '.'))))

            # Filtering incoming data
            if gD:
                own = logic.getCurrentController().owner
                previous_head_position_in_tracker_space = gD['head_position_in_tracker_space']
                if (current_head_position_in_tracker_space - previous_head_position_in_tracker_space).magnitude > 0.1:
                    # print("Data received but invalid")
                    if own['time_from_valid_tracking'] > 1:
                        gD['head_position_in_tracker_space'] = current_head_position_in_tracker_space
                        # print("Updating head position anyway")
                        own['time_from_valid_tracking'] = 0
                else:
                    gD["head_position_in_tracker_space"] = current_head_position_in_tracker_space
                    # print('Data received and valid')
                    own['time_from_valid_tracking'] = 0
            else:
                gD['head_position_in_tracker_space'] = current_head_position_in_tracker_space
                # print('Data received and valid')

        except socket.error:
            # print('No data received')
            pass


########################################################################################################################

# Initialization


def init(own):
    # create a socket using IPV4 address family and UDP protocol
    try:
        global skt
        skt = Socket(socket.AF_INET, socket.SOCK_DGRAM)

    except:
        raise Exception('!!! Unable to create socket, networking initialization failed')
        pass

    own['networking_init'] = True


########################################################################################################################

# Module execution entry point


def main(cont):
    own = cont.owner

    # Initialize networking if not already done
    if 'networking_init' not in own:
        init(own)

    # exit Game Engine if ESC key is pressed
    elif (logic.keyboard.events[bge.events.ESCKEY] == logic.KX_INPUT_JUST_ACTIVATED or
                  logic.keyboard.events[bge.events.ESCKEY] == logic.KX_INPUT_ACTIVE or
                  logic.keyboard.events[bge.events.ESCKEY] == bge.logic.KX_INPUT_JUST_RELEASED):

        # close the socket before exiting
        if skt:
            skt.close()

        # end the Game Engine
        logic.endGame()

    else:
        skt.receive()
