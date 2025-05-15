from machine import Pin, I2S
import time

bck_pin = Pin(14)
ws_pin = Pin(15)
sd_pin = Pin(32)

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
    while True:
        play_wav("honk.wav")
        time.sleep(3)
except KeyboardInterrupt:
    print("Playback stopped by user.")

