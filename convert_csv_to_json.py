import csv
import json
from pathlib import Path


HONK = "honk"
NOISE = "noise"
WAV = "wav"

entries = {}
with open("sound/metadata/UrbanSound8K.csv") as f:
    reader = csv.reader(f, delimiter=' ', quotechar='|')
    next(reader)
    for row in reader:
        parts = row[0].split(",")
        label = HONK if parts[-1] == "car_horn" else NOISE
        entries[parts[0]] = label

# pathlib.Path("sound", "metadata").with_suffix(".json").write_text(json.dumps(entries, indent=4))
path: Path
for i, path in enumerate(Path("sound", "audio").iterdir()):
    if path.suffix == f".{WAV}":
        name = f"{HONK if entries[path.name] == HONK else NOISE}.{i}.{WAV}"
        path.rename(path.parent / name)
