import random

from machine import Pin, I2S
import time


bck_pin = Pin(14)
ws_pin = Pin(15)
sd_pin = Pin(32)

red_pin = Pin(18, Pin.OUT)
yellow_pin = Pin(5, Pin.OUT)
green_pin = Pin(17, Pin.OUT)
pins = [red_pin, yellow_pin, green_pin]

def init_i2s():
    return I2S(
        0,
        sck=bck_pin,
        ws=ws_pin,
        sd=sd_pin,
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=16000,
        ibuf=4096
    )


def play_wav(filename):
    audio_out = init_i2s()
    try:
        with open(filename, "rb") as f:
            f.seek(44)  # skip WAV header
            while True:
                data = f.read(1024)
                if not data:
                    break
                audio_out.write(data)
    except Exception as e:
        print("Error playing file:", e)
    finally:
        audio_out.deinit()


try:
    last_timestamp = time.time()
    current_timestamp = time.time()
    current_color = 0 # 0 red, 1 yellow, 2 green

    values = [0, 0]
    i = 0

    honk_button = Pin(23, Pin.IN, Pin.PULL_UP)
    while True:
        pins[current_color].value(1)
        current_timestamp = time.time()
        if current_timestamp - last_timestamp > (6 if current_color == 0 else 1):
            last_timestamp = current_timestamp
            pins[current_color].value(0)
            current_color += 1
            if current_color == 3:
                current_color = 0

        values[i] = not honk_button.value()
        i += 1
        if i == len(values):
            i = 0
        if all(values) and current_color == 0:
            last_timestamp = current_timestamp
            number = random.randint(1, 5)
            play_wav(f"audio{number}.wav")
            print("HORN")
            time.sleep(3)
except KeyboardInterrupt:
    print("Playback stopped by user.")
