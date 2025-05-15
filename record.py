from machine import I2S, Pin
import time

# Pin setup (update if needed)
bck_pin = Pin(14)
ws_pin = Pin(15)
sd_pin = Pin(32)

# Initialize I2S in RX mode
audio_in = I2S(0, sck=bck_pin, ws=ws_pin, sd=sd_pin,
               mode=I2S.RX,
               bits=16,
               format=I2S.MONO,
               rate=16000,
               ibuf=4096)

buffer = bytearray(1024)

def write_wav_header(f, data_size):
    f.seek(0)
    f.write(b'RIFF')
    f.write((36 + data_size).to_bytes(4, 'little'))
    f.write(b'WAVEfmt ')
    f.write((16).to_bytes(4, 'little'))  # PCM chunk size
    f.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
    f.write((1).to_bytes(2, 'little'))   # Num channels
    f.write((16000).to_bytes(4, 'little'))  # Sample rate
    f.write((16000 * 2).to_bytes(4, 'little'))  # Byte rate
    f.write((2).to_bytes(2, 'little'))   # Block align
    f.write((16).to_bytes(2, 'little'))  # Bits per sample
    f.write(b'data')
    f.write(data_size.to_bytes(4, 'little'))

print("Start recording... Press Ctrl+C to stop.")

with open("mic_record.wav", "wb") as f:
    # Write placeholder header
    f.write(b'\x00' * 44)
    data_size = 0

    try:
        while True:
            num_bytes = audio_in.readinto(buffer)
            if num_bytes:
                f.write(buffer[:num_bytes])
                data_size += num_bytes
    except KeyboardInterrupt:
        print("Stopping recording...")

    # Update WAV header with correct sizes
    write_wav_header(f, data_size)

print("Recording saved to mic_record.wav")
