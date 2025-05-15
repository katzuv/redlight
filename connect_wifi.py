import network
import time

def connect_wifi(ssid):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid)  # no password
        timeout = 10
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                print('Failed to connect.')
                return False
            time.sleep(1)
    print('Network config:', wlan.ifconfig())
    return True

SSID = 'ECE-Conference'

connect_wifi(SSID)
