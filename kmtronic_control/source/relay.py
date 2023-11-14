from requests import get
import re
import time


class KMTronicBreaker:

    def __init__(self, ip):
        self.ip = ip  # ethernet breaker IP address

    def set_channel_states(self, channel, state=None):
        """
        Combination of all posibble option of setting up the relays.
        For setting up one channel chose channel to change (int) and whether it should be turned on of not (1-on 0-off).
        For changing state of channel choose which one to switch (int).
        For setting up all channels at once use string only containing eight time 0 for off and 1 for on('01010101').
        First position refers to first channel and last for eight.

        Sets a channel state. Can be used to set state for all channels at once. Since the web server implemented in
        the ethernet breaker uses only GET function and the response code is always success, a check needs to be
        made by sending another GET after a brief 0.5s delay and compare the two records (what was sent and what was
        read back).
        """
        if type(channel) == str:
            self.set_channels(channel[::-1])
        else:
            if state is None:
                self.change_channel_state(channel)
            else:
                self.set_channel_state(channel, state)
        time.sleep(0.25)

    def set_channels(self, channel: str):
        """
        setting up all the channels at once, parameter channel has to be 8 characters long containing only 1 and 0
        set_channels("01010101") - relay1=0 relay2=1...
        """
        if re.match("^[01]*$", channel) and len(channel) == 8:
            hex_str = '%0*X' % ((len(channel) + 3) // 4, int(channel, 2))
            status = get('http://' + self.ip + '/FFE0' + hex_str).text
            self.show_state(status)
        else:
            print("wrong input")

    def set_channel_state(self, channel: int, state: int):
        """
        setting up one channel at the time, parameter channel stands for relay to switch and state for if on or off
        (1-on 0-off) both has to be int set_channel_state(6, 1)
        """
        if channel in range(1, 9) and state in range(0, 2):
            status = get('http://' + self.ip + '/FF0' + str(channel) + "0" + str(state)).text
            self.show_state(status)
        else:
            print("channel out of range (1-8)")

    def change_channel_state(self, channel: int):
        """
        changing state of one relay, channel stands for relay of which state is switched, has to be int
        change_channel_state(5)
        """
        if channel in range(1, 9):
            status = get('http://' + self.ip + '/relays.cgi?relay=' + str(channel)).text
            self.show_state(status)
        else:
            print("channel out of range (1-8)")

    def show_state(self, status):
        """
        show state prints out current state of all channels
        x = string of 8 bits representing state of respective channels
        """
        i = 1
        for x in [x for x in status.split("\n") if "Status" in x]:
            x = x.replace("Status: ", "").replace(" ", "").replace("\r", "")
            for st in x:
                # print(f"relay{i}: {st}")
                i += 1

    def state(self):
        channel = 0
        status = get('http://' + self.ip + '/relays.cgi?relay=' + str(channel)).text
        for x in [x for x in status.split("\n") if "Status" in x]:
            x = x.replace("Status: ", "").replace(" ", "").replace("\r", "")
            return x


if __name__ == '__main__':
    relay = KMTronicBreaker("192.168.0.199")
    start_time = time.time()
    for i in range(1):
        relay.set_channel_states("11001100")
        relay.set_channel_states(6, 1)
        relay.set_channel_states(5)
        relay.set_channel_states("00000000")
        print("--- %s seconds ---" % (time.time() - start_time))
    print("--- FINISHED %s seconds ---" % (time.time() - start_time))
    relay.state()
