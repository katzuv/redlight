import time
import ei_classify
import microphone

def get_timestamp():
    t = time.localtime()
    return "{:02}:{:02}:{:02}".format(t[3], t[4], t[5])

print("👂 Listening for honks...")

while True:
    features = microphone.record()
    result = ei_classify.classify(features)

    if not result:
        print("Failed to classify audio.")
        continue

    label = result["label"]
    confidence = result["confidence"]

    if label == "honk":
        print("Honk detected at", get_timestamp())
    else:
        print("Heard:", label, f"({confidence:.2f})")
