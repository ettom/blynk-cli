#!/usr/bin/env python3.7
"""Small python script to interact with the blynk HTTP api."""
import sys
import requests

# If you are hosting your own blynk-server, add the url here.

server = "http://blynk-cloud.com"

# Configure your devices here.
# If your devices are wired so that a pin value of LOW is the "on" state,
# change the <default state> field in the tuple for that device from 0 to 1.
# This might happen if your relays are wired as normally closed.

all_devices = {"<device name>": ("<pin>", "<auth_token>", "<default_state>", "<group>"),
               "bedroom_light": ("V3", "<auth_token>", 0, "bedroom"),
               "kitchen_light": ("d2", "<auth_token>", 1, "kitchen"),
               "temperature":   ("V6", "<auth_token>"),
               "humidity":      ("V5", "<auth_token>")}


# Add the names of devices that are not supposed to be toggled on/off here.
# If a device is not listed here it must have a 0/1 in its <default_state> field.
exclude = ("temperature", "humidity")

# Add the names of device groups/rooms here. All devices that have the name of
# the group as the last field in their tuple will respond.
groups = ("bedroom", "kitchen")


def set_to_state(device, value):
    """Set a device to the required state."""
    value ^= all_devices[device][2]
    pin, auth_token = all_devices[device][0], all_devices[device][1]
    requests.get(f"{server}/{auth_token}/update/{pin}?value={value}")


def get_state(device):
    """Get device state."""
    pin, auth_token = all_devices[device][0], all_devices[device][1]
    r = requests.get(f"{server}/{auth_token}/get/{pin}")
    state = float(r.json()[0])
    if state.is_integer():
        state = int(state)

    return state if state not in (0, 1) else int(device not in exclude and state ^ all_devices[device][2])


def flip_state(device):
    """Invert device state."""
    set_to_state(device, get_state(device) ^ 1)


def apply_function(devices, func, *args):
    """Given a function as an argument, apply function to all given devices.

    Extra arguments, if given, are passed to the function.
    """
    for device in devices:
        func(device, *args)


def get_status_as_dict(devices):
    """Return status of given devices in dict format."""
    status = {}
    for device in devices:
        status[device] = get_state(device)

    return status


def print_status(devices):
    """Prettyprint status of devices."""
    status_dict = get_status_as_dict(devices)
    table = ""
    max_len = max(len(x) for x in status_dict) + 1
    for device, status in status_dict.items():
        table += f"{device: <{max_len}}: {status: <{3}} \n"
    table = table[:-1:]
    return table


def choose_devices(action, *args):
    """Choose which devices to modify."""
    if args[0] in ("all", "a"):
        devices_to_modify = [device for device in all_devices.keys()
                             if device not in exclude
                             or action[:1] in ("s", "p")]
    elif args[0] in groups:
        devices_to_modify = [device for device in all_devices.keys()
                             if args[0] in all_devices[device]]
    else:
        devices_to_modify = args

    return devices_to_modify


def take_action(action, *args):
    """Take action on given devices."""
    if action[:1] == "f":          # flip
        apply_function(args, flip_state)
    elif action[:2] == "of":       # off
        apply_function(args, set_to_state, 0)
    elif action == "on":           # on
        apply_function(args, set_to_state, 1)
    elif action[:1] == "j":        # just
        apply_function(args, set_to_state, 1)
        devices_to_turn_off = [device for device in all_devices.keys()
                               if device not in exclude
                               and all_devices[device][-1] in [all_devices[device][-1] for device in args]
                               and device not in args]
        apply_function(devices_to_turn_off, set_to_state, 0)
    elif action[:1] == "p":        # print
        print(print_status(args))
    elif action[:1] == "s":        # status
        print(get_status_as_dict(args) if len(args) != 1 else get_state(*args))


if __name__ == "__main__":
    # last argument is action to take, others are devices to modiy
    *args, action = sys.argv[1:]

    devices_to_modify = choose_devices(action, *args)
    take_action(action, *devices_to_modify)
