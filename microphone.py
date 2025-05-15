from machine import I2S, Pin

class Microphone:
    def __init__(self, sck_pin=26, ws_pin=25, sd_pin=33, sample_rate=16000):
        self.i2s = I2S(
            0,
            sck=Pin(sck_pin),
            ws=Pin(ws_pin),
            sd=Pin(sd_pin),
            mode=I2S.RX,
            bits=16,
            format=I2S.MONO,
            rate=sample_rate,
            ibuf=4096
        )
        self.sample_rate = sample_rate

    def read(self, num_samples):
        buf = bytearray(num_samples * 2)  # 16 bits = 2 bytes per sample
        num_read = self.i2s.readinto(buf)
        if num_read:
            return buf
        return None

    def deinit(self):
        self.i2s.deinit()
