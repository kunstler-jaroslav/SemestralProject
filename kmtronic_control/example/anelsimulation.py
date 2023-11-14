from anel_power_control import AnelPowerControl
from pprint import pprint
import time


anel = AnelPowerControl('127.0.0.1', auth=('admin', 'anel'))


def print_data(device):
    print("Device data:")
    pprint(device.data)


def bottom_to_top(device):
    device[0].on()
    device[1].on()
    device[2].on()
    device[3].on()
    device[4].on()
    device[5].on()
    device[6].on()
    device[7].on()


def top_to_bottom(device):
    device['Nr. 8'].off()
    device['Nr. 7'].off()
    device['Nr. 6'].off()
    device['Nr. 5'].off()
    device['Nr. 4'].off()
    device['Nr. 3'].off()
    device['Nr. 2'].off()
    device['Nr. 1'].off()


if __name__ == "__main__":
    print(anel[0])
    print(anel.__getitem__(1))
    bottom_to_top(anel)
    top_to_bottom(anel)
    pprint(list(anel))
    print(anel[2].off())


